# vim: set sw=4 ts=4 et tw=78:# /
# **** BEGIN LICENSE BLOCK *****
#  Version: MPL 1.1/GPL 2.0/LGPL 2.1
# 
#  The contents of this file are subject to the Mozilla Public License Version
#  1.1 (the "License"); you may not use this file except in compliance with
#  the License. You may obtain a copy of the License at
#  http://www.mozilla.org/MPL/
# 
#  Software distributed under the License is distributed on an "AS IS" basis,
#  WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
#  for the specific language governing rights and limitations under the
#  License.
# 
#  The Original Code is the Narcissus JavaScript engine.
# 
#  The Initial Developer of the Original Code is
#  Brendan Eich <brendan@mozilla.org>.
#  Portions created by the Initial Developer are Copyright (C) 2004
#  the Initial Developer. All Rights Reserved.
# 
#  Contributor(s):
#    Tom Austin <taustin@ucsc.edu>
#    Brendan Eich <brendan@mozilla.org>
#    Shu-Yu Guo <shu@rfrn.org>
#    Dave Herman <dherman@mozilla.com>
#    Dimitris Vardoulakis <dimvar@ccs.neu.edu>
#    Patrick Walton <pcwalton@mozilla.com>
#
#  Translated into Python syntax:
#    Evgen Burzak <buzzilo@gmail.com>
# 
#  Alternatively, the contents of this file may be used under the terms of
#  either the GNU General Public License Version 2 or later (the "GPL"), or
#  the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
#  in which case the provisions of the GPL or the LGPL are applicable instead
#  of those above. If you wish to allow use of your version of this file only
#  under the terms of either the GPL or the LGPL, and not to allow others to
#  use your version of this file under the terms of the MPL, indicate your
#  decision by deleting the provisions above and replace them with the notice
#  and other provisions required by the GPL or the LGPL. If you do not delete
#  the provisions above, a recipient may use your version of this file under
#  the terms of any one of the MPL, the GPL or the LGPL.
# 
#  ***** END LICENSE BLOCK ***** */

#
#  Narcissus - JS implemented in JS.
# 
#  Lexical scanner.
# 

__author__ = "Burzak"
__author_email__ = "buzzilo@gmail.com"
__date__ = "2011-01-24"

__all__ = ["ParseError", "Tokenizer"]

import defs, ast

# Set constants in the local scope.
defs.map(globals())

class ParseError(Exception): pass

class SyntaxError_(ParseError):
    def __init__(self, message, filename, lineno):
        ParseError.__init__(self, "Syntax error: %s\n%s:%s" %
                (message, filename, lineno))

# Build up a trie of operator tokens.
opTokens = {}
for op, token in defs.opTypeNames :
    if (op == '\n' or op == '.'):
        continue

    node = opTokens
    for i in range(len(op)):
        ch = op[i]
        if ch not in node:
            node[ch] = {}
        node = node[ch]
        node["op"] = op

# FIXME Python internals: +/-inf, nan etc..
def parseInt(x):
    return int(x, 0)

def parseFloat(x):
    return float(x)

class Token : pass

class Tokenizer() :
    """
    /*
     * Tokenizer :: (source, filename, line number) -> Tokenizer
     */
    """
    def __init__(self, s, f="", l=1):
        self.cursor = 0
        self.source = str(s)
        self.tokens = {}
        self.tokenIndex = 0
        self.lookahead = 0
        self.scanNewlines = False
        self.unexpectedEOF = False
        self.filename = f
        self.lineno = l

    char = property(lambda self: self.source[self.cursor:self.cursor+1])
    # We need to set scanOperand to true here because the first thing
    # might be a regexp.
    done = property(lambda self: self.peek(True) == END)
    token = property(lambda self: self.tokens.get(self.tokenIndex))

    def match(self, tt, scanOperand=False):
        return self.get(scanOperand) == tt or self.unget()

    def mustMatch(self, tt):
        if not self.match(tt):
            raise self.newSyntaxError("Missing " + defs.tokens.get(tt).lower())
        return self.token

    def peek(self, scanOperand=False):
        if self.lookahead:
            next = self.tokens.get((self.tokenIndex + self.lookahead) & 3)
            if self.scanNewlines and (getattr(next, "lineno", None) !=
                    getattr(self, "lineno", None)):
                tt = NEWLINE
            else:
                tt = getattr(next, "type_", None)
        else:
            tt = self.get(scanOperand)
            self.unget()
        return tt

    def peekOnSameLine(self, scanOperand=False):
        self.scanNewlines = True
        tt = self.peek(scanOperand)
        self.scanNewlines = False
        return tt

    # Eat comments and whitespace.
    def skip(self) :
        input = self.source
        while True :
            ch = self.char
            self.cursor += 1
            next = self.char

            if (ch == '\n' and not self.scanNewlines) :
                self.lineno += 1

            elif (ch == '/' and next == '*') :
                self.cursor += 1
                while True :
                    ch = self.char
                    self.cursor += 1
                    if (ch == None) :
                        raise self.newSyntaxError("Unterminated comment")

                    if (ch == '*') :
                        next = self.char
                        if (next == '/') :
                            self.cursor += 1
                            break
                    elif (ch == '\n') :
                        self.lineno += 1

            elif (ch == '/' and next == '/') :
                self.cursor += 1
                while True :
                    ch = self.char
                    self.cursor += 1
                    if (ch == None) :
                        return

                    if (ch == "\n") :
                        self.lineno += 1
                        break

            elif (ch != ' ' and ch != '\t') :
                self.cursor -= 1
                return

    # Lex the exponential part of a number, if present. Return True iff an
    # exponential part was found.
    def lexExponent(self) :
        input = self.source
        next = self.char
        if (next == 'e' or next == 'E') :
            self.cursor += 1
            ch = self.char
            self.cursor += 1
            if (ch == '+' or ch == '-') :
                ch = self.char
                self.cursor += 1

            if (ch < '0' or ch > '9') :
                raise self.newSyntaxError("Missing exponent")

            while True :
                ch = self.char
                self.cursor += 1
                if not (ch >= '0' and ch <= '9'): break
            self.cursor -= 1

            return True

        return False

    def lexZeroNumber(self, ch) :
        token = self.token
        input = self.source
        token.type_ = NUMBER

        ch = self.char
        self.cursor += 1
        if (ch == '.') :
            while True :
                ch = self.char
                self.cursor += 1
                if not (ch >= '0' and ch <= '9'): break
            self.cursor -= 1

            self.lexExponent()
            token.value = parseFloat(input[token.start: self.cursor])

        elif (ch == 'x' or ch == 'X') :
            while True :
                ch = self.char
                self.cursor += 1
                if not ((ch >= '0' and ch <= '9') or (ch >= 'a' and ch <= 'f') or
                        (ch >= 'A' and ch <= 'F')): 
                    break
            self.cursor -= 1

            token.value = parseInt(input[token.start: self.cursor])

        elif (ch >= '0' and ch <= '7') :
            while True :
                ch = self.char
                self.cursor += 1
                if not (ch >= '0' and ch <= '7'): break
            self.cursor -= 1

            token.value = parseInt(input[token.start: self.cursor])

        else :
            self.cursor -= 1
            self.lexExponent()     # 0E1, &c.
            token.value = 0

    def lexNumber(self, ch) :
        token = self.token
        input = self.source
        token.type_ = NUMBER

        floating = False
        while True :
            ch = self.char
            self.cursor += 1
            if (ch == '.' and not floating) :
                floating = True
                ch = self.char
                self.cursor += 1
            if not (ch >= '0' and ch <= '9'): break

        self.cursor -= 1

        exponent = self.lexExponent()
        floating = floating or exponent

        str_ = input[token.start: self.cursor]
        token.value = floating and parseFloat(str_) or parseInt(str_)

    def lexDot(self, ch) :
        token = self.token
        input = self.source
        next = self.char
        if (next >= '0' and next <= '9') :
            while True:
                ch = self.char
                self.cursor += 1
                if not (ch >= '0' and ch <= '9'): break
            self.cursor -= 1

            self.lexExponent()

            token.type_ = NUMBER
            token.value = parseFloat(input[token.start: self.cursor])
        else :
            token.type_ = DOT
            token.assignOp = None
            token.value = '.'

    def lexString(self, ch) :
        token = self.token
        input = self.source
        token.type_ = STRING

        hasEscapes = False
        delim = ch
        while True :
            ch = self.char
            self.cursor += 1
            if ch == delim : break
            if (self.cursor == len(input)) :
                raise self.newSyntaxError("Unterminated string literal")
            if (ch == '\\') :
                hasEscapes = True
                self.cursor += 1
                if (self.cursor == len(input)) :
                    raise self.newSyntaxError("Unterminated string literal")

        if hasEscapes :
            # safely translate JS string into python bytes
            token.value = ast.literal_eval(input[token.start: self.cursor]) # no eval() here!
        else :
            token.value = input[token.start + 1: self.cursor - 1]

    def lexRegExp(self, ch) :
        token = self.token
        input = self.source
        token.type_ = REGEXP
        regexp = ""
        modifiers = ""

        startRegexp = self.cursor
        while True :
            ch = self.char
            self.cursor += 1
            if (ch == '\\') :
                self.cursor += 1

            elif (ch == '[') :
                while True :
                    if (ch == None) :
                        raise self.newSyntaxError("Unterminated character class")

                    if (ch == '\\') :
                        self.cursor += 1

                    ch = self.char
                    self.cursor += 1
                    if ch == ']': break;
                    regexp += ch

            elif (ch == None) :
                raise self.newSyntaxError("Unterminated regex")

            if ch == '/': break

        regexp = input[startRegexp:self.cursor-1]

        while True :
            ch = self.char
            self.cursor += 1
            if not (ch >= 'a' and ch <= 'z') : break
            modifiers += ch

        self.cursor -= 1

        token.value = {
            "regexp" : regexp,
            "modifiers" : modifiers
        }
        #token.value = str(input[token.start: self.cursor]) # no evals!

    def lexOp(self, ch) :
        token = self.token
        input = self.source

        # A bit ugly, but it seems wasteful to write a trie lookup routine
        # for only 3 characters...
        node = opTokens[ch]
        next = self.char
        if (next in node) :
            node = node[next]
            self.cursor += 1
            next = input[self.cursor]
            if (next in node) :
                node = node[next]
                self.cursor += 1
                next = input[self.cursor]

        op = node["op"]
        if (defs.assignOps.has_key(op) and input[self.cursor] == '=') :
            self.cursor += 1
            token.type_ = ASSIGN
            token.assignOp = defs.tokenIds[dict(defs.opTypeNames)[op]]
            op += '='
        else :
            token.type_ = defs.tokenIds[dict(defs.opTypeNames)[op]]
            token.assignOp = None

        token.value = op

    # FIXME: Unicode escape sequences
    # FIXME: Unicode identifiers
    def lexIdent(self, ch) :
        token = self.token
        input = self.source

        while True :
            ch = self.char
            self.cursor += 1
            if not ((ch >= 'a' and ch <= 'z') or (ch >= 'A' and ch <= 'Z') or
                    (ch >= '0' and ch <= '9') or ch == '$' or ch == '_'):
                break

        self.cursor -= 1  # Put the non-word character back.

        id = input[token.start: self.cursor]
        token.type_ = defs.jsKeywords.get(id) or IDENTIFIER
        token.value = id

    def get(self, scanOperand=False) :
        """
        /*
         * Tokenizer.get :: void -> token.type_
         *
         * Consume input *only* if there is no lookahead.
         * Dispatch to the appropriate lexing function depending on the input.
         */
        """
        while (self.lookahead) :
            self.lookahead -= 1
            self.tokenIndex = (self.tokenIndex + 1) & 3
            token = self.tokens.get(self.tokenIndex)
            if (token.type_ != NEWLINE or self.scanNewlines) :
                return token.type_

        self.skip()

        self.tokenIndex = (self.tokenIndex + 1) & 3
        token = self.tokens.get(self.tokenIndex)
        if (not token) :
            token = Token()
            self.tokens[self.tokenIndex] = token

        input = self.source
        if (self.cursor == len(input)) :
            token.type_ = END
            if not hasattr(token, "lineno"):
                token.lineno = 1
            return token.type_

        token.start = self.cursor
        token.lineno = self.lineno

        ch = input[self.cursor]
        self.cursor += 1
        if ((ch >= 'a' and ch <= 'z') or \
                (ch >= 'A' and ch <= 'Z') or \
                ch == '$' or ch == '_') :
            self.lexIdent(ch)
        elif (scanOperand and ch == '/') :
            self.lexRegExp(ch)
        elif (ch in opTokens) :
            self.lexOp(ch)
        elif (ch == '.') :
            self.lexDot(ch)
        elif (ch >= '1' and ch <= '9') :
            self.lexNumber(ch)
        elif (ch == '0') :
            self.lexZeroNumber(ch)
        elif (ch == '"' or ch == "'") :
            self.lexString(ch)
        elif (self.scanNewlines and ch == '\n') :
            token.type_ = NEWLINE
            token.value = '\n'
            self.lineno += 1
        else :
            raise self.newSyntaxError("Illegal token")

        token.end = self.cursor
        return token.type_

    """
    /*
     * Tokenizer.unget :: void -> undefined
     *
     * Match depends on unget returning undefined.
     */
    """
    def unget(self) :
        self.lookahead += 1
        if (self.lookahead == 4): raise "PANIC: too much lookahead!"
        self.tokenIndex = (self.tokenIndex - 1) & 3

    def newSyntaxError(self, m) :
        e = SyntaxError_(m, self.filename, self.lineno)
        e.source = self.source
        if self.lookahead:
            e.cursor = self.tokens[(self.tokenIndex + self.lookahead) & 3].start

        return e
