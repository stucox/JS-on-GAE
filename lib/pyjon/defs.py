#!/usr/bin/python2.5
# -*- coding: utf-8 -*-
#
# JS constants, tokens and keywords

import sys, re

def err(msg):
    sys.stderr.write(str(msg) + "\n")

jsTokens = dict(enumerate((
        # End of source.
        "END",

        # Operators and punctuators. Some pair-wise order matters, e.g. (+, -)
        # and (UNARY_PLUS, UNARY_MINUS).
        "\n", ";",
        ",",
        "=",
        "?", ":", "CONDITIONAL",
        "||",
        "&&",
        "|",
        "^",
        "&",
        "==", "!=", "===", "!==",
        "<", "<=", ">=", ">",
        "<<", ">>", ">>>",
        "+", "-",
        "*", "/", "%",
        "!", "~", "UNARY_PLUS", "UNARY_MINUS",
        "++", "--",
        ".",
        "[", "]",
        "{", "}",
        "(", ")",

        # Nonterminal tree node type codes.
        "SCRIPT", "BLOCK", "LABEL", "FOR_IN", "CALL", "NEW_WITH_ARGS", "INDEX",
        "ARRAY_INIT", "OBJECT_INIT", "PROPERTY_INIT", "GETTER", "SETTER",
        "GROUP", "LIST", "LET_BLOCK", "ARRAY_COMP", "GENERATOR", "COMP_TAIL",

        # Terminals.
        "IDENTIFIER", "NUMBER", "STRING", "REGEXP",

        # Head comments
        "HEADER",

        # Keywords.
        "break",
        "case", "catch", "const", "continue",
        "debugger", "default", "delete", "do",
        "else", "enum",
        "false", "finally", "for", "function",
        "if", "in", "instanceof",
        "let",
        "new", "null",
        "return",
        "switch",
        "this", "throw", "true", "try", "typeof",
        "var", "void",
        "yield",
        "while", "with",
    )))

# Virtual namespaces
virtualNamespace = ("public", "hidden", "static", "global", "frozen",
                        "final", "sealed", "internal", "override")

# JooScript tokens
jooTokens = dict(enumerate((
    
        # Keywords
        "class", "package", "import",
        "as", "role", 
        
        # Namespaces
        "self", "root", "unit", "glob",

        # Null object
        "none",

        # "And" and "or" is an keywords
        #"and", "or", "not"

        ) + virtualNamespace, len(jsTokens)))

jooTokens.update(jsTokens)

statementStartTokens = [
    "break",
    "const", "continue",
    "debugger", "do",
    "for",
    "if",
    "return",
    "switch",
    "throw", "try",
    "var",
    "yield",
    "while", "with",
]

#def build(targ):
    
    #global opTypeNames, jsKeywords, jooKeywords, assignOps
    #global opRegExpSrc, opRegExp, fpRegExp, reRegExp
    #global tokensAll

# Operator and punctuator mapping from token to tree node type name.
# NB: because the lexer doesn't backtrack, all token prefixes must themselves
# be valid tokens (e.g. !== is acceptable because its prefixes are the valid
# tokens != and !).
opTypeNames = [
        ('\n',   "NEWLINE"),
        (';',    "SEMICOLON"),
        (',',    "COMMA"),
        ('?',    "HOOK"),
        (':',    "COLON"),
        ('||',   "OR"),
        ('&&',   "AND"),
        ('|',    "BITWISE_OR"),
        ('^',    "BITWISE_XOR"),
        ('&',    "BITWISE_AND"),
        ('===',  "STRICT_EQ"),
        ('==',   "EQ"),
        ('=',    "ASSIGN"),
        ('!==',  "STRICT_NE"),
        ('!=',   "NE"),
        ('<<',   "LSH"),
        ('<=',   "LE"),
        ('<',    "LT"),
        ('>>>',  "URSH"),
        ('>>',   "RSH"),
        ('>=',   "GE"),
        ('>',    "GT"),
        ('++',   "INCREMENT"),
        ('--',   "DECREMENT"),
        ('+',    "PLUS"),
        ('-',    "MINUS"),
        ('*',    "MUL"),
        ('/',    "DIV"),
        ('%',    "MOD"),
        ('!',    "NOT"),
        ('~',    "BITWISE_NOT"),
        ('.',    "DOT"),
        ('[',    "LEFT_BRACKET"),
        (']',    "RIGHT_BRACKET"),
        ('{',    "LEFT_CURLY"),
        ('}',    "RIGHT_CURLY"),
        ('(',    "LEFT_PAREN"),
        (')',    "RIGHT_PAREN")
    ]

jsKeywords = {}
jooKeywords = {}

# Define const END, etc., based on the token names.  Also map name to index.
tokenIds = {}

# JavaScript
for i, t in jsTokens.copy().iteritems():
    if re.match(r'^[a-z]', t):
        const_name = t.upper()
        jsKeywords[t] = i
        jooKeywords[t] = i
    elif re.match(r'^\W', t):
        const_name = dict(opTypeNames)[t]
    else:
        const_name = t
    globals()[const_name] = i
    tokenIds[const_name] = i
    jsTokens[t] = i

# JooScript
for i, t in jooTokens.copy().iteritems():
    if re.match(r'^[a-z]', t):
        const_name = t.upper()
        jooKeywords[t] = i
    elif re.match(r'^\W', t):
        const_name = dict(opTypeNames)[t]
    else:
        const_name = t
    globals()[const_name] = i
    tokenIds[const_name] = i
    jooTokens[t] = i

assignOps = {}

# Map assignment operators to their indexes in the tokens array.
for i, t in enumerate(['|', '^', '&', '<<', '>>', '>>>', '+', '-', '*', '/', '%']):
    assignOps[t] = jsTokens[t]
    # FIXME
    #assignOps[t] = jooTokens[t]
    assignOps[i] = t

isStatementStartCode = {}
for i in range(len(statementStartTokens)) :
    isStatementStartCode[jsKeywords[statementStartTokens[i]]] = True

tokens = {}
tokens.update(jsTokens)
tokens.update(jooTokens)

def map(obj):
    for const_name, i in tokenIds.iteritems():
        obj[const_name] = i

def tokenstr(tt):
    t = tokens[tt]
    if re.match(r'^\W', t):
        return dict(opTypeNames)[t]
    return t.upper()

class Object: pass

class StringMap() :
    def __init__(self) :
        self.table = Object()
        self.size = 0

    has = lambda self, x : hasattr(self.table, x)

    def set(self, x, v) :
        if (not hasattr(self.table, x)) :
            self.size += 1
        setattr(self.table, x, v)

    get = lambda self, x : getattr(self.table, x, None)

    def getDef(self, x, thunk) :
        if (not hasattr(self.table, x)) :
            self.size += 1
            self.table[x] = thunk()

        return self.table[x]

    def forEach(self, f) :
        table = self.table
        for key in table :
            f(self, key, table[key])

    def toString(self) : return "[object StringMap]"

# non-destructive stack
class Stack() :
    def __init__(self, elts=None) :
        self.elts = elts

    def append(self, x) :
        return Stack({"top": x, "rest": self.elts})

    def top(self) :
        if (not self.elts) :
            raise Exception, "empty stack"
        return self.elts.top

    def isEmpty(self) :
        return self.top == None

    def find(self, test) :
        elts = self.elts
        while elts :
            if (test(elts["top"])) :
                return elts["top"]
            elts = elts["rest"]
        return None

    def has(self, x) :
        return bool(self.find(lambda elt : elt == x ))

    def forEach(self, f) :
        elts = self.elts
        while elts :
            f(elts["top"])
            elts = elts["rest"]
