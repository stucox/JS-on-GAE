#!/usr/bin/python2.5
# -*- coding: utf-8 -*-
# -*- Mode: JS; tab-width: 4; indent-tabs-mode: nil; -*-
#  vim: set sw=4 ts=4 et tw=78:
#  ***** BEGIN LICENSE BLOCK *****
# 
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
#    JT Olds <jtolds@xnet5.com>
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
#  ***** END LICENSE BLOCK ***** 

#
#  Narcissus - JS implemented in JS.
# 
#  Parser.
#

__author__ = "JT Olds"
__author_email__ = "jtolds@xnet5.com"
__date__ = "2009-03-24"

__author__ = "Burzak"
__author_email__ = "buzzilo@gmail.com"
__date__ = "2011-01-24"

__all__ = ["parse"]

import re, sys
import defs, lexer

defs.map(globals())

class Node(list):
    def __init__(self, t, type_=None, args=[], **attrs):
        list.__init__(self)

        token = t.token

        if token:
            if type_:
                self.type_ = type_
            elif "type" in attrs:
                self.type_ = attrs["type"]
            else:
                self.type_ = getattr(token, "type_", None)
            self.value = token.value
            self.lineno = token.lineno
            
            # Start and end are file positions for error handling.
            self.start = token.start
            self.end = token.end
        else:
            self.type_ = type_
            self.lineno = t.lineno
        self.tokenizer = t

        for arg in args:
            self.append(arg)

        for attr in attrs:
            if attr != "type":
                setattr(self, attr, attrs[attr])

        self.commentBefore = ""
        self.whitespaces = ""
        #self.commentBefore = t.commentBefore
        #t.commentBefore = ""
        #self.whitespaces = getattr(t.token, "whitespaces", "") 
        #if self.whitespaces: t.token.whitespaces = ""

    type = property(lambda self: defs.tokenstr(self.type_))

    # Always use push to add operands to an expression, to update start and end.
    def append(self, kid, numbers=[]):
        if kid:
            if getattr(self, "start", None) < kid.start:
                self.start = kid.start
            if getattr(self, "end", None) < kid.end:
                self.end = kid.end
        return list.append(self, kid)

    indentLevel = 0

    def __str__(self):
        a = list((str(i), v) for i, v in enumerate(self))
        for attr in dir(self):
            if attr[0] == "_": continue
            elif attr == "tokenizer":
                a.append((attr, "[object Object]"))
            #elif attr == "whitespaces": a.append((attr, repr(getattr(self, attr))))
            elif attr in ("append", "count", "extend", "getSource", "index",
                    "insert", "pop", "remove", "reverse", "sort", "type_",
                    "target", "filename", "indentLevel", "type"):
                continue
            elif attr in ("commentBefore", "whitespaces", "endWhitespaces"): 
                continue
            else:
                a.append((attr, getattr(self, attr)))
        if len(self): a.append(("length", len(self)))
        a.sort(lambda a, b: cmp(a[0], b[0]))
        INDENTATION = "    "
        Node.indentLevel += 1
        n = Node.indentLevel
        s = "{\n%stype: %s" % ((INDENTATION * n), defs.tokenstr(self.type_))
        for i, value in a:
            s += ",\n%s%s: " % ((INDENTATION * n), i)
            if i == "value" and self.type_ == REGEXP:
                s += "/%s/%s" % (value["regexp"], value["modifiers"])
            elif value is None:
                s += "null"
            elif value is False:
                s += "false"
            elif value is True:
                s += "true"
            elif type(value) == list:
                s += ','.join((str(x) for x in value))
            else:
                s += str(value)
        Node.indentLevel -= 1
        n = Node.indentLevel
        s += "\n%s}" % (INDENTATION * n)
        return s
    __repr__ = __str__

    def getSource(self):
        if getattr(self, "start", None) is not None:
            if getattr(self, "end", None) is not None:
                return self.tokenizer.source[self.start:self.end]
            return self.tokenizer.source[self.start:]
        if getattr(self, "end", None) is not None:
            return self.tokenizer.source[:self.end]
        return self.tokenizer.source[:]

    filename = property(lambda self: self.tokenizer.filename)

    def __nonzero__(self): return True

def pushDestructuringVarDecls(n, s) :
    """
    /*
     * pushDestructuringVarDecls :: (node, hoisting node) -> void
     *
     * Recursively add all destructured declarations to varDecls.
     */
    """
    for sub in n:
        if (sub.type_ == IDENTIFIER) :
            s.varDecls.append(sub)
        else:
            pushDestructuringVarDecls(sub, s)

def scriptInit() :
    return { "type": SCRIPT,
             "funDecls": [],
             "varDecls": [],
             "modDecls": [],
             "impDecls": [],
             "expDecls": [],
             "loadDeps": [],
             "isRootNode": True,
             "hasEmptyReturn": False,
             "hasReturnWithValue": False,
             "isGenerator": False };

def blockInit() :
    return { 
            "type": BLOCK, 
            "varDecls": [] }

def Script(tz, inFunction=False) :
    """
    /*
     * Script :: (tokenizer, boolean) -> node
     *
     * Parses the toplevel and function bodies.
     */
    """
    n = Node(tz, SCRIPT, **scriptInit())
    x = StaticContext(tz, n, n, inFunction, False, NESTING_TOP)
    x.Statements(n)
    return n

# NESTING_TOP: top-level
# NESTING_SHALLOW: nested within static forms such as { ... } or labeled statement
# NESTING_DEEP: nested within dynamic forms such as if, loops, etc.
NESTING_TOP = 0
NESTING_SHALLOW = 1
NESTING_DEEP = 2;

DECLARED_FORM = 0
EXPRESSED_FORM = 1
STATEMENT_FORM = 2

# JSContext was merged with StaticContext
class StaticContext(): 
    """
    Parsed a portion of JavaScript code into node tree.
    """
    def __init__(self, tokenizer, parentScript, parentBlock, 
                    inFunction, inForLoopInit, nesting, **kwargs): 
        self.tz = tokenizer
        self.funDecls = kwargs.get("funDecls") or []
        self.varDecls = kwargs.get("varDecls") or []
        self.ecmaStrictMode = kwargs.get("ecmaStrictMode") or False
        self.inFunction = inFunction or kwargs.get("inFunction") or False
        self.inForLoopInit = inForLoopInit or kwargs.get("inForLoopInit") or False
        self.nesting = nesting or kwargs.get("nesting") or NESTING_TOP
        self.parentScript = parentScript or kwargs.get("parentScript")
        self.parentBlock = parentBlock or kwargs.get("parentBlock")
        self.parenFreeMode = kwargs.get("parenFreeMode") or False
        self.ecma3OnlyMode = kwargs.get("ecma3OnlyMode") or False
        self.allLabels = kwargs.get("allLabels") or defs.Stack()
        self.currentLabels = kwargs.get("currentLabels") or defs.Stack()
        self.labeledTargets = kwargs.get("labeledTargets") or defs.Stack()
        self.defaultTarget = kwargs.get("defaultTarget")

    def update(self, **ext):
        args = dict(
            funDecls = self.funDecls,
            varDecls = self.varDecls,
            inFunction = self.inFunction,
            inForLoopInit = self.inForLoopInit,
            ecma3OnlyMode = self.ecma3OnlyMode,
            nesting = self.nesting,
            parentScript = self.parentScript,
            parentBlock = self.parentBlock,
            parenFreeMode = self.parenFreeMode,
            allLabels = self.allLabels,
            currentLabels = self.currentLabels,
            labeledTargets = self.labeledTargets,
            defaultTarget = self.defaultTarget
        )
        args.update(ext)
        x = self.__class__(
            self.tz,
            **args
        )
        return x

    def pushLabel(self, label) :
        return self.update( currentLabels = self.currentLabels.append(label),
                            allLabels = self.allLabels.append(label) )

    def pushTarget(self, target) :
        isDefaultTarget = getattr(target, "isLoop", None) or target.type_ == SWITCH

        if (self.currentLabels.isEmpty()) :
            if isDefaultTarget :
                return self.update( defaultTarget = target )
            else:
                return self
            return 

        target.labels = defs.StringMap()
        self.currentLabels.forEach(lambda label : target.labels.set(label, True) )

        if isDefaultTarget : 
            defaultTarget = target 
        else : 
            defaultTarget = self.defaultTarget 

        return self.update(  currentLabels = defs.Stack(),
                             labeledTargets = self.labeledTargets.append(target),
                             defaultTarget = defaultTarget )

    def nest(self, atLeast) :
        nesting = max(self.nesting, atLeast)
        if nesting != self.nesting :
            return self.update( nesting = nesting )
        else :
            return self

    def MaybeLeftParen(self) :
        if (self.parenFreeMode):
            if self.tz.match(LEFT_PAREN):
                return LEFT_PAREN 
            else:
                return END

        return self.tz.mustMatch(LEFT_PAREN).type_

    def MaybeRightParen(self, p) :
        if (p == LEFT_PAREN) :
            self.tz.mustMatch(RIGHT_PAREN);

    def Statements(self, n) :
        """
        /*
         * Statements :: (tokenizer, compiler context, node) -> void
         *
         * Parses a sequence of Statements.
         */
        """
        done = self.tz.done
        try :
            while ( not self.tz.done and self.tz.peek(True) != RIGHT_CURLY):
                n.append(self.Statement())
        except Exception, e :
            if (self.tz.done):
                self.tz.unexpectedEOF = True
            raise

    def Block(self) :
        self.tz.mustMatch(LEFT_CURLY)
        n = Node(self.tz, BLOCK, **blockInit())
        x2 = self.update( parentBlock=n ).pushTarget(n)
        x2.Statements(n)
        self.tz.mustMatch(RIGHT_CURLY)
        return n

    def Statement(self):
        tt = self.tz.get()

        stmt_definition = tt in defs.tokens and \
                defs.tokens.get(tt).title() + "Definition" or None

        # Cases for statements ending in a right curly return early, avoiding the
        # common semicolon insertion magic after this switch.
        #
        # DECLARED_FORM extends funDecls of x, STATEMENT_FORM doesn't.
        if tt == FUNCTION:
            return self.FunctionDefinition(True, (self.nesting != NESTING_TOP) and \
                                                    STATEMENT_FORM or DECLARED_FORM);

        # Skip identifier definition in statement form, it will defined as expression.
        elif stmt_definition and tt != IDENTIFIER and \
                callable(getattr(self, stmt_definition, None)):
            #defs.err( (tt, stmt_definition))
            if len(self.stmtStack) > 1:
                type_ = STATEMENT_FORM
            else:
                type_ = DECLARED_FORM
            kwargs = {}
            if tt == FUNCTION: kwargs["requireName"] = True
            n = getattr(self, stmt_definition)(type_, **kwargs)
            if n.type_ not in [RETURN]:
                return n

        elif tt == LEFT_CURLY:
            n = Node(self.tz, **blockInit())
            x2 = self.update( parentBlock=n ).pushTarget(n).nest(NESTING_SHALLOW)
            x2.Statements(n)
            self.tz.mustMatch(RIGHT_CURLY)
            #n.endWhitespaces = self.tz.token.whitespaces
            return n

        elif tt == IF:
            n = Node(self.tz)
            n.condition = self.HeadExpression()
            x2 = self.pushTarget(n).nest(NESTING_DEEP)
            n.thenPart = x2.Statement()
            if self.tz.match(ELSE) : n.elsePart = x2.Statement()
            else : n.elsePart = None
            return n

        elif tt == SWITCH:
          # This allows CASEs after a DEFAULT, which is in the standard.
          n = Node(self.tz, cases = [], defaultIndex = -1 )
          n.discriminant = self.HeadExpression()
          x2 = self.pushTarget(n).nest(NESTING_DEEP)
          self.tz.mustMatch(LEFT_CURLY)
          while True :
              tt = self.tz.get()
              if tt == RIGHT_CURLY: break
              elif tt in (CASE, DEFAULT) :
                if tt == DEFAULT:
                    if (n.defaultIndex >= 0) :
                        raise self.tz.newSyntaxError("More than one switch default")

                n2 = Node(self.tz)
                if (tt == DEFAULT) :
                    n.defaultIndex = len(n.cases)
                else :
                    n2.caseLabel = x2.Expression()

              else:
                raise self.tz.newSyntaxError("Invalid switch case")

              self.tz.mustMatch(COLON)
              n2.statements = Node(self.tz, **blockInit())
              while True :
                  tt=self.tz.peek(True)
                  if not (tt != CASE and tt != DEFAULT and \
                          tt != RIGHT_CURLY): break
                  n2.statements.append(x2.Statement())
              n.cases.append(n2)

          return n

        elif tt == FOR:
          n = Node(self.tz, FOR, isLoop=True)
          n2 = None
          if (self.tz.match(IDENTIFIER)) :
              if (self.tz.token.value == "each") :
                  n.isEach = True
              else :
                  self.tz.unget()
          if (not self.parenFreeMode) :
              self.tz.mustMatch(LEFT_PAREN)
          x2 = self.pushTarget(n).nest(NESTING_DEEP)
          x3 = self.update( inForLoopInit = True )
          tt = self.tz.peek()
          if (tt != SEMICOLON) :
              if (tt == VAR or tt == CONST) :
                  self.tz.get()
                  n2 = x3.Variables()
              elif (tt == LET) :
                  self.tz.get()
                  if (self.tz.peek() == LEFT_PAREN) :
                      n2 = x3.LetBlock(False)
                  else :
                      # Let in for head, we need to add an implicit block
                      # around the rest of the for.
                      x3.parentBlock = n
                      n.varDecls = []
                      n2 = x3.Variables()
              else :
                  n2 = x3.Expression()

          if (n2 and self.tz.match(IN)) :
              n.type_ = FOR_IN
              n.object = x3.Expression()
              if (n2.type_ == VAR or n2.type_ == LET) :
                  c = n2

                  # Destructuring turns one decl into multiples, so either
                  # there must be only one destructuring or only one
                  # decl.
                  if (len(c) != 1 and len(n2.destructurings) != 1) :
                      raise SyntaxError_("Invalid for..in left-hand side",
                                            self.tz.filename, n2.lineno)
                  if (len(n2.destructurings) > 0) :
                      n.iterator = n2.destructurings[0]
                  else :
                      n.iterator = c[0]
                  n.varDecl = n2

              else :
                  if (n2.type_ == ARRAY_INIT or n2.type_ == OBJECT_INIT) :
                      n2.destructuredNames = x3.checkDestructuring(n2)
                  n.iterator = n2
          else :
              n.setup = n2
              self.tz.mustMatch(SEMICOLON)
              if (getattr(n, "isEach", None)) :
                  raise self.tz.newSyntaxError("Invalid for each..in loop")
              if (self.tz.peek() == SEMICOLON) : 
                n.condition = None
              else :
                n.condition = x3.Expression()

              self.tz.mustMatch(SEMICOLON)
              tt2 = self.tz.peek()
              if self.parenFreeMode:
                isStatement = tt2 == LEFT_CURLY or defs.isStatementStartCode[tt2]
              else:
                isStatement = tt2 == RIGHT_PAREN
              
              if isStatement:
                n.update = None
              else:
                n.update = x3.Expression()

          if (not self.parenFreeMode) :
              self.tz.mustMatch(RIGHT_PAREN)
          n.body = x2.Statement()
          return n

        elif tt == WHILE:
          n = Node(self.tz, isLoop = True )
          n.condition = self.HeadExpression()
          x2 = self.pushTarget(n).nest(NESTING_DEEP)
          n.body = x2.Statement()
          return n

        elif tt == DO:
          n = Node(self.tz, isLoop = True )
          x2 = self.pushTarget(n).nest(NESTING_DEEP)
          n.body = x2.Statement()
          self.tz.mustMatch(WHILE)
          n.condition = self.HeadExpression()
          if (not self.ecmaStrictMode) :
              # <script language="JavaScript"> (without version hints) may need
              # automatic semicolon insertion without a newline after do-while.
              # See http://bugzilla.mozilla.org/show_bug.cgi?id=238945.
              self.tz.match(SEMICOLON)
              return n

        elif tt in (BREAK, CONTINUE):
          n = Node(self.tz)

          # handle the |foo: break foo| corner case
          x2 = self.pushTarget(n)

          if (self.tz.peekOnSameLine() == IDENTIFIER) :
              self.tz.get()
              n.label = self.tz.token.value

          if getattr(n, "label", None) :
            n.target = x2.labeledTargets.find(lambda target : target.labels.has(n.label))
          else :
            n.target = x2.defaultTarget

          if (not n.target) :
              raise self.tz.newSyntaxError("Invalid " + ((tt == BREAK) and "break" or "continue"))

          if (not getattr(n.target, "isLoop", None) and tt == CONTINUE) :
              raise self.tz.newSyntaxError("Invalid continue")

        elif tt == TRY:
          n = Node(self.tz, catchClauses = [])
          n.tryBlock = self.Block()
          while (self.tz.match(CATCH)) :
              n2 = Node(self.tz)
              p = self.MaybeLeftParen()
              tt = self.tz.get()
              if tt in (LEFT_BRACKET, LEFT_CURLY): 
                # Destructured catch identifiers.
                self.tz.unget()
                n2.varName = self.DestructuringExpression(True)

              elif tt == IDENTIFIER:
                n2.varName = self.tz.token.value

              else:
                raise self.tz.newSyntaxError("missing identifier in catch")

              if (self.tz.match(IF)) :
                  if (self.ecma3OnlyMode) :
                      raise self.tz.newSyntaxError("Illegal catch guard")
                  if (len(n.catchClauses) and not n.catchClauses.top().guard) :
                      raise self.tz.newSyntaxError("Guarded catch after unguarded")
                  n2.guard = self.Expression()

              self.MaybeRightParen(p)
              n2.block = self.Block()
              n.catchClauses.append(n2)

          if (self.tz.match(FINALLY)) :
              n.finallyBlock = self.Block()

          if (not len(n.catchClauses) and not n.finallyBlock) :
              raise self.tz.newSyntaxError("Invalid try statement")

          return n

        elif tt in (CATCH, FINALLY):
          raise self.tz.newSyntaxError(defs.tokens[tt] + " without preceding try")

        elif tt == THROW:
          n = Node(self.tz)
          n.exception = self.Expression()

        elif tt == RETURN:
          n = self.ReturnOrYield()

        elif tt == WITH:
          n = Node(self.tz)
          n.object = self.HeadExpression()
          x2 = self.pushTarget(n).nest(NESTING_DEEP)
          n.body = x2.Statement()
          return n

        elif tt in (VAR, CONST):
          n = self.Variables()

        elif tt == LET:
          if (self.tz.peek() == LEFT_PAREN) :
              n = self.LetBlock(True)
          else :
              n = self.Variables()

        elif tt == DEBUGGER:
          n = Node(self.tz)

        elif tt in (NEWLINE, SEMICOLON):
          n = Node(self.tz, SEMICOLON)
          n.expression = None
          return n

        else:
            if tt == IDENTIFIER:
                self.tz.scanOperand = False
                tt = self.tz.peek()
                self.tz.scanOperand = True
                if tt == COLON:
                    label = self.tz.token.value
                    ss = self.stmtStack
                    i = len(ss) - 1
                    while i >= 0:
                        if getattr(ss[i], "label", None) == label:
                            raise self.tz.newSyntaxError("Duplicate label")
                        i -= 1
                    self.tz.get()
                    n = Node(self.tz, LABEL)
                    n.label = label
                    n.statement = self.nest(n, self.Statement)
                    # TODO translate me
                    #n.statement = Statement(t, x.pushLabel(label).nest(NESTING_SHALLOW));
                    #n.target = (n.statement.type === LABEL) ? n.statement.target : n.statement;
                    return n

            # Expression statement.
            # We unget the current token to parse the expression as a whole.
            n = Node(self.tz, SEMICOLON)
            self.tz.unget()
            n.expression = self.Expression()
            n.end = n.expression.end

        self.MagicalSemicolon()
        return n

    def MagicalSemicolon(self):
        # check that statement is commited by newline or semicolon
        if self.tz.lineno == self.tz.token.lineno:
            tt = self.tz.peekOnSameLine()
            if tt not in (END, NEWLINE, SEMICOLON, RIGHT_CURLY):
                raise self.tz.newSyntaxError("Missing ; before statement")
        self.tz.match(SEMICOLON)

    # not in a function context
    #def returnDefinition(self, *args):
        #raise self.tz.newSyntaxError("Invalid return")

    def ReturnOrYield(self) :
        tt = self.tz.token.type_

        parentScript = self.parentScript

        if (tt == RETURN) :
            if (not self.inFunction) :
                raise self.tz.newSyntaxError("Return not in function")
        else : # /* if (tt == YIELD) */ 
            if (not self.inFunction) :
                raise self.tz.newSyntaxError("Yield not in function")
            parentScript.isGenerator = True

        n = Node(self.tz, value=None)

        tt2 = self.tz.peek(True)
        if (tt2 != END and tt2 != NEWLINE and \
            tt2 != SEMICOLON and tt2 != RIGHT_CURLY \
            and (tt != YIELD or \
                (tt2 != tt and tt2 != RIGHT_BRACKET and tt2 != RIGHT_PAREN and \
                 tt2 != COLON and tt2 != COMMA))) :
            if (tt == RETURN) :
                n.value = self.Expression()
                parentScript.hasReturnWithValue = True
            else :
                n.value = self.AssignExpression()
        elif (tt == RETURN) :
            parentScript.hasEmptyReturn = True

        # Disallow return v in generator.
        if (parentScript.hasReturnWithValue and parentScript.isGenerator) :
            raise self.tz.newSyntaxError("Generator returns a value")

        return n

    def FunctionDefinition(self, requireName, functionForm) :
        """
        /*
         * FunctionDefinition :: (tokenizer, compiler context, boolean,
         *                        DECLARED_FORM or EXPRESSED_FORM or STATEMENT_FORM)
         *                    -> node
         */
        """
        f = Node(self.tz, params=[])
        if (f.type_ != FUNCTION):
            if f.value == "get": f.type_ = GETTER 
            else: f.type_ = SETTER
        if (self.tz.match(IDENTIFIER)):
            f.name = self.tz.token.value
        elif (requireName):
            raise self.tz.newSyntaxError("missing function identifier")

        x2 = self.__class__(self.tz, None, None, True, False, NESTING_TOP)

        self.tz.mustMatch(LEFT_PAREN)
        if (not self.tz.match(RIGHT_PAREN)) :
            while True:
                tt = self.tz.get()
                if tt in (LEFT_BRACKET, LEFT_CURLY):
                    # Destructured formal parameters.
                    self.tz.unget()
                    f.params.append(x2.DestructuringExpression())
                elif tt == IDENTIFIER:
                    f.params.append(self.tz.token.value)
                else:
                    raise self.tz.newSyntaxError("missing formal parameter")

                if not self.tz.match(COMMA): break

            self.tz.mustMatch(RIGHT_PAREN)


        # Do we have an expression closure or a normal body?
        tt = self.tz.get()
        if (tt != LEFT_CURLY) :
            self.tz.unget()

        if (tt != LEFT_CURLY) :
            f.body = x2.AssignExpression()
            if (getattr(f.body, "isGenerator", None)):
                raise self.tz.newSyntaxError("Generator returns a value")
        else :
            f.body = Script(self.tz, True)

        if (tt == LEFT_CURLY) :
            self.tz.mustMatch(RIGHT_CURLY)

        f.end = self.tz.token.end
        f.functionForm = functionForm
        if (functionForm == DECLARED_FORM) :
            self.parentScript.funDecls.append(f)
        return f

    def IdentifierDefinition(self):
        self.tz.mustMatch(IDENTIFIER)
        return Node(self.tz)
    
    def Variables(self, letBlock=None):
        """
        /*
         * Variables :: (tokenizer, compiler context) -> node
         *
         * Parses a comma-separated list of var declarations (and maybe
         * initializations).
         */
        """
        tt = self.tz.token.type_;
        if tt in (CONST, VAR):
            s = self.parentScript;
        elif tt == LET:
            s = self.parentBlock;
        elif tt == LEFT_PAREN:
            tt = LET;
            s = letBlock;

        n = Node(self.tz, tt, destructurings = [])

        while True:
            tt = self.tz.get()
            if (tt == LEFT_BRACKET or tt == LEFT_CURLY) :
                # Need to unget to parse the full destructured expression.
                self.tz.unget()

                dexp = self.DestructuringExpression(True)

                n2 = Node(self.tz, IDENTIFIER, 
                                    name = dexp, 
                                    readOnly = n.type_ == CONST )
                n.append(n2)
                pushDestructuringVarDecls(n2.name.destructuredNames, s)
                n.destructurings.append({"exp": dexp, "decl": n2})

                if (self.inForLoopInit and self.tz.peek() == IN) :
                    continue

                self.tz.mustMatch(ASSIGN)
                if (self.tz.token.assignOp):
                    raise self.tz.newSyntaxError("Invalid variable initialization")

                n2.initializer = self.AssignExpression()

                continue


            if (tt != IDENTIFIER):
                raise self.tz.newSyntaxError("missing variable name")

            n2 = Node(self.tz, IDENTIFIER, 
                        name = self.tz.token.value, 
                        readOnly = n.type_ == CONST)
            n.append(n2)
            s.varDecls.append(n2)

            if (self.tz.match(ASSIGN)) :
                if (self.tz.token.assignOp) :
                    raise self.tz.newSyntaxError("Invalid variable initialization")

                n2.initializer = self.AssignExpression()

            if not self.tz.match(COMMA): break

        return n

    def LetBlock(self, isStatement) :
        """
        /*
         * LetBlock :: (tokenizer, compiler context, boolean) -> node
         *
         * Does not handle let inside of for loop init.
         */
        """
        # self.tz.token.type must be LET
        n = Node(self.tz, LET_BLOCK, varDecls=[])
        self.tz.mustMatch(LEFT_PAREN)
        n.variables = self.Variables(n)
        self.tz.mustMatch(RIGHT_PAREN)

        if (isStatement and self.tz.peek() != LEFT_CURLY) :
            """
            /*
             * If this is really an expression in let statement guise, then we
             * need to wrap the LET_BLOCK node in a SEMICOLON node so that we pop
             * the return value of the expression.
             */
            """
            n2 = Node(self.tz, SEMICOLON, expression=n)
            isStatement = False

        if (isStatement):
            n.block = self.Block()
        else:
            n.expression = self.AssignExpression()

        return n

    def checkDestructuring(self, n, simpleNamesOnly) :
        if (n.type_ == ARRAY_COMP):
            raise self.tz.newSyntaxError("Invalid array comprehension left-hand side")
        if (n.type_ != ARRAY_INIT and n.type_ != OBJECT_INIT):
            return

        lhss = {}
        i = 0
        while i < len(n) :
            nn = n[i]
            if not nn: continue
            if (nn.type_ == PROPERTY_INIT) :
                sub = nn[1]
                idx = nn[0].value
            elif (n.type_ == OBJECT_INIT) :
                # Do we have destructuring shorthand {foo, bar}?
                sub = nn
                idx = nn.value
            else :
                sub = nn
                idx = i

            if (sub.type_ == ARRAY_INIT or sub.type_ == OBJECT_INIT) :
                lhss[idx] = self.checkDestructuring(sub, simpleNamesOnly)
            else :
                if (simpleNamesOnly and sub.type != IDENTIFIER) :
                    # In declarations, lhs must be simple names
                    raise self.tz.newSyntaxError("missing name in pattern")

                lhss[idx] = sub

            i += 1

        return lhss

    def DestructuringExpression(simpleNamesOnly) :
        n = self.PrimaryExpression()
        # Keep the list of lefthand sides for varDecls
        n.destructuredNames = self.checkDestructuring(n, simpleNamesOnly)
        return n

    def GeneratorExpression(e) :
        return Node(t, GENERATOR,
                         expression = e,
                         tail = self.ComprehensionTail())

    def ComprehensionTail(self) :
        #var body, n, n2, n3, p

        # self.tz.token.type must be FOR
        body = Node(self.tz, COMP_TAIL)

        while True:
            # Comprehension tails are always for..in loops.
            n = Node(self.tz, FOR_IN, isLoop = True)
            if (self.tz.match(IDENTIFIER)) :
                # But sometimes they're for each..in.
                if (self.tz.token.value == "each"):
                    n.isEach = True
                else:
                    self.tz.unget()

            p = self.MaybeLeftParen()
            tt = self.tz.get()
            if tt in (LEFT_BRACKET, LEFT_CURLY): 
                self.tz.unget()
                # Destructured left side of for in comprehension tails.
                n.iterator = self.DestructuringExpression()

            elif tt == IDENTIFIER:
                n.iterator = n3 = Node(self.tz, IDENTIFIER)
                n3.name = n3.value
                n.varDecl = n2 = Node(self.tz, VAR)
                n2.append(n3)
                self.parentScript.varDecls.append(n3)
                # Don'self.tz add to varDecls since the semantics of comprehensions is
                # such that the variables are in their own function when
                # desugared.

            else:
                raise self.tz.newSyntaxError("missing identifier")

            self.tz.mustMatch(IN)
            n.object = self.Expression()
            self.MaybeRightParen(p)
            body.append(n)
            if not self.tz.match(FOR): break

        # Optional guard.
        if (self.tz.match(IF)):
            body.guard = self.HeadExpression()

        return body

    def HeadExpression(self) :
        p = self.MaybeLeftParen()
        n = self.ParenExpression()
        self.MaybeRightParen(p)
        if (p == END and not getattr(n, "parenthesized", None)) :
            tt = self.tz.peek()
            if (tt != LEFT_CURLY and not defs.isStatementStartCode[tt]):
                raise self.tz.newSyntaxError("Unparenthesized head followed by unbraced body")
        return n

    def ParenExpression(self) :
        # Always accept the 'in' operator in a parenthesized expression,
        # where it's unambiguous, even if we might be parsing the init of a
        # for statement.
        x2 = self.update(inForLoopInit = self.inForLoopInit and \
                            (self.tz.token.type_ == LEFT_PAREN))
        n = x2.Expression()

        if (self.tz.match(FOR)) :
            if (n.type_ == YIELD and not getattr(n, "parenthesized", None)):
                raise self.tz.newSyntaxError("Yield expression must be parenthesized")
            if (n.type_ == COMMA and not getattr(n, "parenthesized", None)):
                raise self.tz.newSyntaxError("Generator expression must be parenthesized")
            n = self.GeneratorExpression(n)

        return n

    def Expression(self):
        """
        /*
         * Expression :: (tokenizer, compiler context) -> node
         *
         * Top-down expression parser matched against SpiderMonkey.
         */
         """
        n = self.AssignExpression()
        if self.tz.match(COMMA):
            n2 = Node(self.tz, COMMA)
            n2.append(n)
            n = n2
            while True:
                n2 = n[-1]
                if n2.type_ == YIELD and not getattr(n2, "parenthesized", None):
                    raise self.tz.newSyntaxError("Yield expression must be parenthesized")
                n.append(self.AssignExpression())
                if not self.tz.match(COMMA): break

        return n

    def AssignExpression(self) :
        # Have to treat yield like an operand because it could be the leftmost
        # operand of the expression.
        if self.tz.match(YIELD, True):
            return self.ReturnOrYield()

        n = Node(self.tz, ASSIGN)
        lhs = self.ConditionalExpression()

        if not self.tz.match(ASSIGN):
            return lhs

        if lhs.type_ in (ARRAY_INIT, OBJECT_INIT): 
            lhs.destructuredNames = self.checkDestructuring(lhs)

        # FALL THROUGH
        elif lhs.type_ in (IDENTIFIER, DOT, INDEX, CALL): pass

        else:
            raise self.tz.newSyntaxError("Bad left-hand side of assignment")

        n.assignOp = self.tz.token.assignOp
        n.append(lhs)
        n.append(self.AssignExpression())

        return n
    
    def ConditionalExpression(self):
        n = self.OrExpression()
        if self.tz.match(HOOK) :
            n2 = n
            n = Node(self.tz, HOOK)
            n.append(n2)
            """
            /*
             * Always accept the 'in' operator in the middle clause of a ternary,
             * where it's unambiguous, even if we might be parsing the init of a
             * for statement.
             */
            """
            n.append(self.update(inForLoopInit=False).AssignExpression())
            if not self.tz.match(COLON):
                raise self.tz.newSyntaxError("missing : after ?")
            n.append(self.AssignExpression())

        return n

    def OrExpression(self) :
        n = self.AndExpression()
        while self.tz.match(OR):
            n2 = Node(self.tz)
            n2.append(n)
            n2.append(self.AndExpression())
            n = n2

        return n

    def AndExpression(self) :
        n = self.BitwiseOrExpression()
        while (self.tz.match(AND)) :
            n2 = Node(self.tz)
            n2.append(n)
            n2.append(self.BitwiseOrExpression())
            n = n2

        return n

    def BitwiseOrExpression(self):
        n = self.BitwiseXorExpression()
        while (self.tz.match(BITWISE_OR)) :
            n2 = Node(self.tz)
            n2.append(n)
            n2.append(self.BitwiseXorExpression())
            n = n2

        return n

    def BitwiseXorExpression(self):
        n = self.BitwiseAndExpression()
        while (self.tz.match(BITWISE_XOR)) :
            n2 = Node(self.tz)
            n2.append(n)
            n2.append(self.BitwiseAndExpression())
            n = n2

        return n

    def BitwiseAndExpression(self):
        n = self.EqualityExpression()
        while (self.tz.match(BITWISE_AND)) :
            n2 = Node(self.tz)
            n2.append(n)
            n2.append(self.EqualityExpression())
            n = n2

        return n

    def EqualityExpression(self):
        n = self.RelationalExpression()
        while (self.tz.match(EQ) or self.tz.match(NE) or \
               self.tz.match(STRICT_EQ) or self.tz.match(STRICT_NE)) :
            n2 = Node(self.tz)
            n2.append(n)
            n2.append(self.RelationalExpression())
            n = n2

        return n

    def RelationalExpression(self):
        """
        /*
         * Uses of the in operator in shiftExprs are always unambiguous,
         * so unset the flag that prohibits recognizing it.
         */
        """
        x2 = self.update(inForLoopInit=False)
        n = x2.ShiftExpression()
        while ((self.tz.match(LT) or self.tz.match(LE) or self.tz.match(GE) or self.tz.match(GT) or
               (not self.inForLoopInit and self.tz.match(IN)) or
               self.tz.match(INSTANCEOF))) :
            n2 = Node(self.tz)
            n2.append(n)
            n2.append(x2.ShiftExpression())
            n = n2

        return n

    def ShiftExpression(self):
        n = self.AddExpression()
        while (self.tz.match(LSH) or self.tz.match(RSH) or self.tz.match(URSH)) :
            n2 = Node(self.tz)
            n2.append(n)
            n2.append(self.AddExpression())
            n = n2

        return n

    def AddExpression(self):
        n = self.MultiplyExpression()
        while (self.tz.match(PLUS) or self.tz.match(MINUS)) :
            n2 = Node(self.tz)
            n2.append(n)
            n2.append(self.MultiplyExpression())
            n = n2

        return n

    def MultiplyExpression(self):
        n = self.UnaryExpression()
        while (self.tz.match(MUL) or self.tz.match(DIV) or self.tz.match(MOD)) :
            n2 = Node(self.tz)
            n2.append(n)
            n2.append(self.UnaryExpression())
            n = n2

        return n

    def UnaryExpression(self):
        tt = self.tz.get(True)
        
        if tt in (DELETE, VOID, TYPEOF, NOT, BITWISE_NOT, PLUS, MINUS):
            if (tt == PLUS):
                n = Node(self.tz, UNARY_PLUS)
            elif (tt == MINUS):
                n = Node(self.tz, UNARY_MINUS)
            else:
                n = Node(self.tz)
            n.append(self.UnaryExpression())

        elif tt in (INCREMENT, DECREMENT):
            # Prefix increment/decrement.
            n = Node(self.tz)
            n.append(self.MemberExpression(True))

        else:
            self.tz.unget()
            n = self.MemberExpression(True)

            # Don'self.tz look across a newline boundary for a postfix {in,de}crement.
            if (self.tz.tokens[(self.tz.tokenIndex + self.tz.lookahead - 1) & 3].lineno ==
                self.tz.lineno) :
                if (self.tz.match(INCREMENT) or self.tz.match(DECREMENT)) :
                    n2 = Node(self.tz, postfix = True)
                    n2.append(n)
                    n = n2

        return n

    def MemberExpression(self, allowCallSyntax) :
        n = n2 = None

        if self.tz.match(NEW) :
            n = Node(self.tz)
            n.append(self.MemberExpression(False))
            if (self.tz.match(LEFT_PAREN)) :
                n.type_ = NEW_WITH_ARGS
                n.append(self.ArgumentList())
        else :
            n = self.PrimaryExpression()

        while True :
            tt = self.tz.get()
            if tt == END: break
            elif tt == DOT:
                n2 = Node(self.tz)
                n2.append(n)
                self.tz.mustMatch(IDENTIFIER)
                n2.append(Node(self.tz))

            elif tt == LEFT_BRACKET:
                n2 = Node(self.tz, INDEX)
                n2.append(n)
                n2.append(self.Expression())
                self.tz.mustMatch(RIGHT_BRACKET)

            elif tt == LEFT_PAREN:
                if (allowCallSyntax) :
                    n2 = Node(self.tz, CALL)
                    n2.append(n)
                    n2.append(self.ArgumentList())
                else:
                    self.tz.unget()
                    return n

            else:
                self.tz.unget()
                return n

            n = n2

        return n

    def ArgumentList(self):
        n = Node(self.tz, LIST)
        if (self.tz.match(RIGHT_PAREN, True)):
            return n

        while True:
            n2 = self.AssignExpression()
            if (n2.type_ == YIELD and not getattr(n2, "parenthesized", None) \
                    and self.tz.peek() == COMMA):
                raise self.tz.newSyntaxError("Yield expression must be parenthesized")
            if (self.tz.match(FOR)) :
                n2 = self.GeneratorExpression(n2)
                if (len(n) > 1 or self.tz.peek(True) == COMMA):
                    raise self.tz.newSyntaxError("Generator expression must be parenthesized")
            n.append(n2)
            if not self.tz.match(COMMA): break

        self.tz.mustMatch(RIGHT_PAREN)

        return n

    def PrimaryExpression(self):
        tt = self.tz.get(True)

        if tt == FUNCTION:
            n = self.FunctionDefinition(False, EXPRESSED_FORM)

        elif tt == LEFT_BRACKET:
            n = Node(self.tz, ARRAY_INIT)
            while True :
                tt = self.tz.peek(True)
                if (tt == RIGHT_BRACKET): break
                if (tt == COMMA) :
                    self.tz.get()
                    n.append(None)
                    continue
                n.append(self.AssignExpression())
                if (tt != COMMA and not self.tz.match(COMMA)):
                    break
                tt = self.tz.peek(True)

            # If we matched exactly one element and got a FOR, we have an
            # array comprehension.
            if (len(n) == 1 and self.tz.match(FOR)) :
                n2 = Node(self.tz, ARRAY_COMP, expression=n[0], 
                            tail=self.ComprehensionTail())
                n = n2
            self.tz.mustMatch(RIGHT_BRACKET)

        elif tt == LEFT_CURLY:
            n = Node(self.tz, OBJECT_INIT)

            if not self.tz.match(RIGHT_CURLY) :
                while True :
                    tt = self.tz.get()
                    if ((self.tz.token.value == "get" or self.tz.token.value == "set") and \
                            self.tz.peek() == IDENTIFIER) :
                        if (self.ecma3OnlyMode):
                            raise self.tz.newSyntaxError("Illegal property accessor")
                        n.append(self.FunctionDefinition(True, EXPRESSED_FORM))
                    else :
                        if tt in (IDENTIFIER, NUMBER, STRING):
                            id = Node(self.tz, IDENTIFIER)

                        elif tt == RIGHT_CURLY:
                            if (self.ecma3OnlyMode):
                                raise self.tz.newSyntaxError("Illegal trailing ,")

                        else:
                            if (self.tz.token.value in definitions.keywords) :
                                id = Node(self.tz, IDENTIFIER)
                                break
                            raise self.tz.newSyntaxError("Invalid property name")

                        if (self.tz.match(COLON)) :
                            n2 = Node(self.tz, PROPERTY_INIT)
                            n2.append(id)
                            n2.append(self.AssignExpression())
                            n.append(n2)
                        else :
                            # Support, e.g., |var {x, y} = o| as destructuring shorthand
                            # for |var {x: x, y: y} = o|, per proposed JS2/ES4 for JS1.8.
                            if (self.tz.peek() != COMMA and self.tz.peek() != RIGHT_CURLY):
                                raise self.tz.newSyntaxError("missing : after property")
                            n.append(id)

                    if not self.tz.match(COMMA): break

                self.tz.mustMatch(RIGHT_CURLY)

        elif tt == LEFT_PAREN:
            n = self.ParenExpression()
            self.tz.mustMatch(RIGHT_PAREN)
            n.parenthesized = True

        elif tt == LET:
            n = self.LetBlock(False)

        elif tt in (NULL, THIS, TRUE, FALSE, 
                    IDENTIFIER, NUMBER, STRING, REGEXP):
            if tt == NUMBER:
                n = Number(self.tz)
            else:
                n = Node(self.tz)

        else:
            raise self.tz.newSyntaxError("missing operand")

        return n

class JSFunction(StaticContext):
    """
    JS function context
    """
    def __init__(self, **kwargs):
        StaticContext.__init__(self, parent.tz, parentScript=kwargs["parentScript"])
        
    def returnDefinition(self, *args):
        n = Node(self.tz)
        tt = self.tz.peekOnSameLine()
        if tt not in (END, NEWLINE, SEMICOLON, RIGHT_CURLY):
            n.value = self.Expression()
        return n

class Number(Node):
    def __init__(self, t):
        Node.__init__(self, t)
        self.isHex = False
        self.integer = False
        #self.isHex = t.token.isHex
        #self.integer = t.token.integer

class Header(Node):
    def __init__(self, t):
        Node.__init__(self, t)

def parse(source, filename=None, starting_line_number=1):
    """Parse some Javascript

    Args:
        source: the Javascript source, as a string
        filename: the filename to include in messages
        starting_line_number: the line number of the first line of the
            passed in source, for output messages
    Returns:
        the parsed source code data structure
    Raises:
        lexer.ParseError
    """
    t = lexer.Tokenizer(source, filename, starting_line_number)
    n = Script(t)
    if not t.done:
        raise t.newSyntaxError("Syntax error")
    return n

