#!/usr/bin/env python

# -*- coding: utf-8 -*-

#
# PyJS, ECMAScript implementation in Python (with some non-standart extendings).
# ------------------------------------------------------------------------------
# 
# Due to similarity of both languages PyJS is basically wrapping pythonic 
# objects and classes with mimics of javascript behavior.
# Although it is not straightforward implementation of ECMA specs as it is mainly being 
# used for script testing.
#
# Author: Evgen Burzak <buzzilo@gmail.com>
#
# Implemented:
# ------------
# __ arithmetic operations: +, -, *, %, ...
# __ bitwise operations: &, |, ^, <<, >>, >>>, ...
# __ comparison: if, else, ==, ===, >, <, >=, ...
# __ functions
# __ prototype property
#
# Partially implemented:
# ----------------
# __ Date
# __ Math object: with (Math) abs(), round() ...
# __ loops: while(), do .. while(), for() ...
# __ try .. catch statement
# __ switch .. case statement
# __ ...
#
# Not implemented:
# ----------------
# __ with statement
# __ ...
#
# Copyright (c) 2010-2011, Evgeny Burzak <buzzilo@gmail.com>
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the <organization> nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

# TODO use indeces for vars

from __future__ import division, with_statement
from functools import wraps
from functools import partial
import functools

"""
ChangeLog

24/01/11

 * Implemented caller property
 * Implemented try-catch clause
 * Throwing exceptions
 * Implemented switch .. case 
 * Other improvements
 
20/01/11
 * Implemented while loop.
 * Implemented instanceof (although no deep checks).
 * Added JS methods parseInt, parseFloat, isNaN.
"""

import re, math, operator
from ctypes import c_int
import os, random

import defs, jsparser, lexer

defs.map(globals())

class JSError(Exception): 
    def __init__(self, message="", lineno=-1, 
                    start=0, end=0, filename="", stack=[]):
        Exception.__init__(self, message)
        self.fileName = filename
        self.lineNumber = lineno
        self.name = self.__class__.__name__
        self.stack = stack

    def get (self, key): pass
    def set (self, key, value): pass

    __call__ = lambda self, this, *args: self.__class__(*args)

    @staticmethod
    def __newInstance__(*args):
        return JSError(*args)

    __str__ = lambda self: "%s: %s [%s, %i]" % (self.name, self.message, 
            self.fileName, self.lineNumber)

class NotImplemented_(JSError): pass
class Warning(JSError): pass # raise warnings as exception in strict mode

# ECMAScript exceptions
class ECMAScriptError(JSError): pass
ECMAScriptError.__name__ = "Error"
class ReferenceError(ECMAScriptError): pass
#class TypeError_(ECMAScriptError): pass
TypeError_ = type("TypeError", (ECMAScriptError,), {})
#class SyntaxError_(ECMAScriptError): pass
SyntaxError_ = type("SyntaxError", (ECMAScriptError,), {})
#class RangeError_(ECMAScriptError): pass
RangeError_ = type("RangeError", (ECMAScriptError,), {})
class URIError(ECMAScriptError): pass

class BreakOutOfLoops(Exception): pass
class ContinueLoops(Exception): pass

class Null():
    __int__ = lambda self: 0
    __nonzero__ = lambda self: False
    __repr__ = lambda self: ""
    __str__ = lambda self: "null"

# types aliases
nan = float('nan')
inf = float('inf')
null = Null()
undefined = None
false = False 
true = True 

#
# type checkers
#

isString = lambda x: isinstance(x, str)
isInt = lambda x: isinstance(x, int)
isFloat = lambda x: isinstance(x, float)
isNumber = lambda x: isinstance(x, (int, float, long)) and not isBoolean(x)
isInfinity = lambda x: x == float("+inf") or x == float("-inf")
# as far as i know NaN is th only value that yields false when compared
# to itself. 
isNaN = lambda x: x != x
isUndefined = lambda x: x == None
isNull = lambda x: id(null) == id(x)
isBoolean = lambda x: isinstance(x, bool) or hasattr(x, '__isbool__')
isObject = lambda x: isinstance(x, JS_Object)
isFunction = lambda x: callable(x)
isXML = lambda x: isinstance(x, XML) or isinstance(x, XMLList)
isArray = lambda x: isinstance(x, array_proto)

#
# conversion routines
#
intRe = re.compile(r'^(-|\+)?\d+$')
floatRe = re.compile(r'^(-|\+)?(\d+)?\.(\d+)$')
shortFloatRe = re.compile(r'^(-|\+)?(\d+)\.(\d+)e\+(\d+)$')
hexRe = re.compile(r'^(-|\+)?0x([0-9a-fA-F]+)$')

def toNumber(y):
    x = None
    if x == 0: x = 0
    elif isNumber(y): x = y
    elif isBoolean(y): x = int(y)
    elif isString(y):
        if y == "":
            x = 0
        else:
            # there is some internal pythonic types like nan and +inf,-inf
            # it may be passed in strings, so using regexp to check
            m = re.match(intRe, y)
            if m: x = int(y)
            else:
                m = re.match(floatRe, y)
                if m: 
                    x = float(y)
                else:
                    m = re.match(shortFloatRe, y)
                    if m:
                        x = float(y)
                    else:
                        m = re.match(hexRe, y)
                        if m: x = int(y, 16)
                        else:
                            x = nan
            """
            try: 
                x = int(y)
            except ValueError:
                try: 
                    x = float(y)
                except ValueError:
                    try:
                        if re.match(hexRe, y): x = int(y, 16)
                        else: x = nan
                    except ValueError: 
                        x = nan
            """
    elif isNull(y):
        x = 0
    elif isObject(y):
        x = toNumber(str_(y))
    else:
        x = nan

    # reflects javascript behavior
    return (x >= 0xfffffffffffffffffff or isinstance(x, long)) \
            and float(x) or x

def toInt(y):
    #print "toInt()", y, type(y)
    x = toNumber(y)
    if isInfinity(x): return x
    elif isNaN(x): return nan
    else: return int(x)

# convertJOVMInternalObjectIntoPythonicNatives()
#
def convert(obj):

    if isinstance(obj, number_proto_):
        if isFloat(obj): return float(obj)
        elif isInt(obj): return int(obj)

    elif isinstance(obj, string_proto):
        return str(obj)

    # fall into recursion ...
    #elif isinstance(obj, object_proto) or isinstance(obj, Globals):
        #return dict([[k, convert(v)] for k, v in obj])

    #elif isinstance(obj, array_proto):
        #return [convert(v) for v in list.__iter__(obj)]

    #elif isinstance(obj, prototype):
        #return dict([[k, convert(v)] for k, v in obj])

    elif isinstance(obj, func_proto):
        return obj

    elif isinstance(obj, Null): 
        return None

    return obj

def ustr(s):
    if isinstance(s, unicode):
        return s.encode('utf-8')
    else:
        return str(s)

# no, these values is pure empiric
def object_prio(obj):
    if isBoolean(obj): return 800
    if isNumber(obj): return 900
    if isArray(obj): return 400
    if isFunction(obj): return 1000
    if isObject(obj): return 500
    #if isString(obj): return 300

def str_(x):
    if isNull(x): return 'null'
    elif isUndefined(x): return 'undefined'
    elif isNaN(x): return 'NaN'
    elif isBoolean(x): return x and 'true' or 'false'
    elif isInfinity(x): 
        if x > 0: return 'Infinity'
        else: return '-Infinity'
    else: 
        if isinstance(x, unicode):
            return ustr(x)
        return str(x)

def int32(x): 
    if isFloat(x): return 0
    else: return c_int(x).value

def typeof(x):
    if isUndefined(x): return 'undefined' 
    elif isFunction(x): return 'function' 
    elif isNull(x): return 'object' 
    elif isObject(x): return 'object' 
    elif isNumber(x): return 'number' 
    elif isString(x): return 'string' 
    elif isBoolean(x): return 'boolean' 
    elif isXML(x): return 'xml' 
    else: return 'object'

# public function decorator
def publicmethod(f):
    def call(this, context, *args):
        return f(context, *args)

    def apply_(this, context, args):
        return f(context, args)

    f.call = call
    f.apply_ = apply_
    return staticmethod(f)

def object_iter(obj):
    # dictonary may change during iteration, if not copyed
    for k, v in obj.__dict__.copy().iteritems():
        # pass some internal props
        if k in ("constructor", "__proto__"): continue
        elif k in illegal.values(): k = "__%s__" % k[2:-2]
        yield (k, v)

interns = ["__init__", "__setitem__", "__getitem__", "__getattr__",
        "__setattr__", "__getattribute__", "__str__", "__repr__", 
        "__iter__", "__dict__"] # "toString", "valueOf"

# dictonary of illegal props
illegal = {
    "__new__": "%%new%%",
    "__init__": "%%init%%",
    "__class__": "%%class%%"
}

#
# JS object, stem class for all JS objects 
#
class JS_Object(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def __setitem__(self, k, v):
        self.__setattr__(k, v)

    def __getitem__(self, k):
        return getattr(self, k)

    def __setattr__(self, k, v):
        #print "setattr()", self, str_(k), v
        if k in illegal: k = illegal[k]
        if k in interns: return
        object.__setattr__(self, str_(k), v)

    def __delattr__(self, k):
        #print self, "delattr()", k
        if k in interns: return
        object.__delattr__(self, k)

    # mask against internal methods
    def __getattribute__(self, k):
        if k in illegal: k = illegal[k]
        return object.__getattribute__(self, k)

    __iter__ = lambda self: object_iter(self)

    # __class__ property is used in jooscript, so
    # need python class getter
    __python_class__ = property(lambda self: object.__getattribute__(self, "__class__"),
                                 lambda self, v: None)

    toString = publicmethod(lambda this, *args: "[object "+this.__python_class__.__name__+"]")

    @publicmethod
    def valueOf(self): 
        """Returns the primitive value of the specified object. Overrides the Object.valueOf method."""
        return

    __str__ = lambda self: self.toString(self)
    __repr__ = lambda self: self.__python_class__.__name__
    __contains__ = lambda self, item: item in object.__getattribute__(self, "__dict__")

class JS_Function(JS_Object):
    __str__ = lambda self: "function "+self.__python_class__.__name__+"(){[internal]}"
    __repr__ = lambda self: self.__python_class__.__name__

# 
# JS_Context
#
class JS_Context(object):
    def __init__(self, context=None, parent=None, scope=None, caller=None):
        if scope == None:
            self.scope = {}
        else:
            self.scope = scope
        self.stack = []
        self.context = context
        self.returnValue = None
        if parent:
            self.parent = parent
            self.globals = parent.globals
            self.root_context = parent.root_context
            self.js_objects = parent.js_objects
            self.strict = parent.strict
        else:
            self.parent = None
            self.root_context = self
        self.caller = caller

    strict = False
    # return value of function
    returnValue = None

    def exec_(self, n):
        #print n
        this = self.context
        if isNull(n) or isUndefined(n) \
            or isString(n) or isNumber(n): 
                return n

        #print n.type, n.lineno
        t = n.type_
        self.stack.append([t, n.lineno])
        try:
            if t == NUMBER: return toNumber(n.value)
            elif t == STRING: return n.value
            elif t == SEMICOLON: 
                if n.expression: 
                    return self.exec_(n.expression)

            elif t == IDENTIFIER: return self.get_(n)
            elif t == ASSIGN: 
                leftExpr = n[0]
                rightExpr = n[1]
                assignOp = n.assignOp
                return self.assign(leftExpr, rightExpr, assignOp)

            elif n.type_ in (VAR, LET, CONST):
                for x in n:
                    self.initVar(x.value, self.exec_(getattr(x, 'initializer', undefined)))
                return None

            elif t == UNARY_PLUS: return +toNumber(self.exec_(n[0]))
            elif t == UNARY_MINUS: return -toNumber(self.exec_(n[0]))
            elif t in (PLUS, MINUS, DIV, MUL, MOD): 
                a = self.exec_(n[0])
                b = self.exec_(n[1])
                #print t, a, b
                if t == PLUS and (isString(a) or isString(b)):
                    return str_(a) + str_(b)
                else:
                    return self.arithmOp(toNumber(a), toNumber(b), t)

            elif t == BITWISE_NOT:
                try: 
                    return ~toInt(self.exec_(n[0]))
                except TypeError:
                    return ~0

            elif t in (BITWISE_OR, BITWISE_AND, BITWISE_XOR,
                    URSH, RSH, LSH):
                x = self.exec_(n[0])
                y = self.exec_(n[1])
                a = toInt(x)
                b = toInt(y)
                #print "!", x, y, a, b
                return self.bitwiseOp(a, b, t)

            # Warning! This operated on the same scope. 
            # You must initialize new JS_Context instance in your own class!
            elif t == SCRIPT: 
                for x in n:
                    self.exec_(x)

            elif t == GROUP: 
                return self.exec_(n[0])

            elif t in (BLOCK, COMMA): 
                last = undefined
                for x in n: 
                    last = self.exec_(x)
                return last

            elif t == ARRAY_INIT: 
                return array_proto(*[self.exec_(x) for x in n])

            elif t == OBJECT_INIT: 
                kwargs = dict([[ustr(x[0].value), self.exec_(x[1])]
                    for x in n if x.type_ == PROPERTY_INIT])
                return object_proto(**kwargs)

            elif t in (DOT, INDEX): return self.get_(n)
            elif t == FUNCTION: return self.funDef(n)
            elif t == CLASS: return self.classDef(n)

            elif t in (NEW, NEW_WITH_ARGS, CALL): 
                #print n
                if n[0].type_ in (DOT, INDEX):
                    this = self.object(n[0])

                fun = self.exec_(n[0])

                if t in (NEW_WITH_ARGS, CALL):
                    args = [self.exec_(x) for x in n[1]]

                if callable(fun):
                    if hasattr(fun, "caller"):
                        setattr(fun, "caller", self.caller)
                    if t == NEW:
                        return fun.__newInstance__()
                    elif t == NEW_WITH_ARGS:
                        return fun.__newInstance__(*args)
                    else:
                        return fun(this, *args)
                else:
                    self.err(TypeError_, "%s is not a function" % str_(fun), n)

            elif t == RETURN: 
                self.returnValue = self.exec_(n.value)
                raise BreakOutOfLoops

            elif t == FOR_IN: 
                self.for_in(ustr(n.iterator.value), 
                                self.exec_(n.object), n.body)

            elif t == FOR: 
                self.for_(n.setup, n.condition, n.update, n.body)

            elif t == WHILE: 
                self.while_(n.condition, n.body)

            elif t == BREAK: 
                raise BreakOutOfLoops

            elif t == CONTINUE: 
                raise ContinueLoops

            elif t == SWITCH: 
                i = 0
                desc = self.exec_(n.discriminant)
                fall = False
                try:
                    for case in n.cases:
                        if case.type_ == CASE:
                            if desc == self.exec_(case.caseLabel):
                                fall = True

                        if fall:
                            for x in case.statements:
                                self.exec_(x)
                        i += 1

                except BreakOutOfLoops: 
                    # raise again if function context
                    if self.caller: raise

            elif t == HOOK: 
                if self.compare(n[0]):
                    return self.exec_(n[1])
                else:
                    return self.exec_(n[2])

            elif t == REGEXP: 
                return self.regexp(n)

            elif t == TRY: 
                try:
                    self.exec_(n.tryBlock)
                except Exception, e:
                    for catch in n.catchClauses:
                        ctx = JS_Context( parent=self )
                        varName = catch.varName
                        if varName:
                            ctx.scope[varName] = e
                        ctx.exec_(catch.block)
                finally:
                    if hasattr(n, "finallyBlock"):
                        self.exec_(n.finallyBlock)

            elif t == THROW: 
                raise self.exec_(n.exception)

            elif t == DECREMENT: 
                x = self.get_(n[0])
                self.assign(n[0], x+1)
                return x

            elif t == INCREMENT:
                x = self.get_(n[0])
                y = 1
                self.assign(n[0], self.assignOp(x, 1, PLUS))
                return x

            elif t == IF: 
                if self.compare(n.condition):
                    self.exec_(n.thenPart)
                elif n.elsePart:
                    self.exec_(n.elsePart)

            elif t == NOT:
                return not self.exec_(n[0])
                
            elif t == AND:
                return self.compare(n[0]) and self.compare(n[1])

            elif t == OR:
                return self.compare(n[0]) or self.compare(n[1])

            elif t in (GT, LT, EQ, NE, GE, LE, 
                    STRICT_EQ, STRICT_NE): 
                return self.compare(n)

            elif t == TRUE: return True
            elif t == FALSE: return False
            elif t == NULL: return null
            #elif t == UNDEFINED: return undefined
            elif t == VOID: 
                self.exec_(n[0])
                return undefined

            elif t == IN:
                return self.exec_(n[0]) in self.exec_(n[1])

            elif t == THIS: return this

            elif t == TYPEOF: 
                try:
                    return typeof(self.exec_(n[0]))
                except ReferenceError:
                    if n[0].type_ == IDENTIFIER:
                        return "undefined"
                    else:
                        raise

            # FIXME it must walk on all __proto__ chain
            elif t == INSTANCEOF: 
                inst = self.exec_(n[0])
                obj = self.exec_(n[1])
                if isinstance(inst, bool): return obj == boolean
                elif isinstance(inst, (int, float)): return obj == number
                elif isinstance(inst, str): return obj == string
                return inst.__proto__ == obj.prototype

            elif t == HEADER:
                pass
                #print n.value

            #elif t == USE:
                #if n.value == 'strict':
                    #self.strict = True

            elif t == DELETE: 
                delattr(self.object(n[0]), self.property(n[0]))

            else:
                self.err(NotImplemented_, n.type, n)

        except (BreakOutOfLoops, ContinueLoops), ex: 
            raise

        except (TypeError_, ReferenceError, NotImplemented_), ex:
            raise

        except Exception, ex:
            #self.err(JSError, ex.message, n)
            raise

    # assign value
    #
    def assign(self, leftExpr, rightExpr, assignOp=None, local=False): 
        tt = leftExpr.type_

        if tt == IDENTIFIER:
            k = ustr(leftExpr.value)
            ctx = self
            while ctx:
                if k in ctx.scope: break
                ctx = ctx.parent
            else:
                ctx = self.root_context

            if assignOp:
                x = self.var(k, leftExpr)
                y = self.exec_(rightExpr)
                #self.scope[k] = self.assignOp(x, y, assignOp)
                #value = self.assign(k, self.assignOp(x, y, assignOp))
                ctx.scope[k] = self.assignOp(x, y, assignOp)

            else:
                #self.scope[k] = self.exec_(rightExpr)
                #value = self.assign(k, self.exec_(rightExpr))
                ctx.scope[k] = self.exec_(rightExpr)

            return ctx.scope[k]

        elif tt in (DOT, INDEX):
            obj = self.object(leftExpr)
            prop = self.property(leftExpr)
            if isUndefined(obj) or isNull(obj):
                self.err(TypeError_, "cannot set property "
                            "%r of %s" % (prop, str_(obj)), n)
            val = self.exec_(rightExpr)
            if assignOp: 
                if tt == DOT:
                    try:
                        x = getattr(obj, prop)
                    except AttributeError, e:
                        x = undefined
                        defs.err("WARNING: undefined attribute " + prop)
                        #self.undefPropErr(prop, n)
                else:  # INDEX
                    try:
                        x = operator.getitem(obj, prop)
                    except (IndexError, AttributeError), e:
                        x = undefined
                        defs.err("WARNING: undefined index " + prop)
                        #self.undefPropErr(prop, n)
                val = self.assignOp(x, val, assignOp)

            if tt == DOT:
                setattr(obj, prop, val)
            else:
                operator.setitem(obj, prop, val)

            return val

    # get identifier or object property
    #
    def get_(self, n):
        if n.type_ == IDENTIFIER: 
            return self.var(ustr(n.value), n)

        else: # => t in (DOT, INDEX)
            obj = self.object(n)
            prop = self.property(n)

            if isNull(obj) or isUndefined(obj):
                self.err(TypeError_, "cannot read property "
                          "%r of %s" % (getattr(prop, 'value', prop), str_(obj)), n)

            #res = getattr(obj, str_(prop), undefined)
            if n.type_ == DOT:
                try:
                    #print "get()", obj, str_(prop)
                    prop = str_(prop)
                    if prop in illegal: prop = illegal[prop]
                    res = getattr(obj, prop)
                except AttributeError, e:
                    res = undefined
                    #self.undefPropErr(prop, n)
            else: # INDEX
                try:
                    res = operator.getitem(obj, prop)
                except (IndexError, AttributeError), e:
                    res = undefined
                    #self.undefPropErr(prop, n)
                except Exception, e:
                    self.err(TypeError_, e, n)

            return res


    # build actual scope
    #
    def actualScope(self):
        scope = {}
        par = self.parent
        branch = [self]
        while par:
            branch.append(par)
            par = par.parent
        branch.reverse()
        for p in branch:
            scope.update(p.scope)
        return scope

    def __getitem__(self, k):
        return self.actualScope().get(k)

    # get variable from scope or global object
    #
    def var(self, var, n):
        value = None
        scope = self.actualScope()

        if var in scope:
            value = scope[var]
        elif var in self.js_objects:
            value = self.js_objects.get(var)
        elif hasattr(self.globals, var):
            value = getattr(self.globals, var)
        elif var == 'Infinity':
            return inf
        elif var == 'NaN':
            return nan
        elif var == 'undefined':
            return undefined
        else:
            self.err(ReferenceError, "%s is not defined" % var, n)
        
        #if isinstance(value, (Undefined, NaN, Null)):
            #self.warn("%s is %s" % (var, str(value)), n)

        #print "var()", var, str(value)
        return value
    
    # get object
    #
    def object(self, n):
        """ returns object from INDEX and DOT nodes 
            or build new from prototype for certain types
        """ 
        obj = self.exec_(n[0])
        if isObject(obj): return obj
        # FIXME this is stupid, no need to build temp object every time, 
        # it's just required to return prototype object, but prototype
        # must be read-only, so that no properties can be assigned or
        # deleted
        elif isBoolean(obj): return bool_proto()
        elif isNumber(obj) or isInfinity(obj) or isNaN(obj): 
            return number_proto(obj)
        elif isString(obj): return string_proto(obj)
        return obj

    # get property of an given object
    #
    def property(self, n):
        if n.type_ == INDEX:
            return self.exec_(n[1])
        elif n.type_ == DOT:
            if n[1].type_ == IDENTIFIER:
                return ustr(n[1].value)
            else:
                raise NotImplemented_, str(n[1].type)

    # arithmetic operations
    #
    def arithmOp(self, x, y, op):
        try:
            if op == PLUS: 
                if isString(x) or isString(y):
                    x = str_(x) + str_(y)
                else: x += y
            elif op == MINUS: x -= y
            elif op == MUL: x *= y
            elif op == DIV: x /= y
            elif op == MOD:
                # there is a difference between py and js modulo interpretation
                # http://stackoverflow.com/questions/43775/modulus-operation-with-negatives-values-weird-thing
                if (x > 0 and y > 0): x = abs(x) % abs(y)
                elif (x < 0 and y < 0): x = -(abs(x) % abs(y))
                elif x < 0: x = -(abs(x) % abs(y))
                else: x = abs(x) % abs(y)
            else: 
                self.err(NotImplemented_, "arithmOp(): %s" % op)

        except TypeError, e:
           x = nan

        except ZeroDivisionError, e:
           if op == MOD: 
               x = nan
           else: 
               # FIXME +0 and -0
               #print "!", x, y, (x < 0 or y < 0)
               x = (x < 0 or y < 0) and -inf or inf

        # reflects javascript behavior
        if isNumber(x) and x >= 0xfffffffffffffffffff: 
            x = float(x)

        return x

    # bitwise operations
    #
    def bitwiseOp(self, x, y, op):
        """in javascript, bitwise operators yields int32 
        """
        if isInfinity(x): x = 0
        if isInfinity(y) and op != URSH: y = 0
        try:
            if op == BITWISE_OR: 
                x = int32(int(x) | int(y))
            elif op == BITWISE_XOR: 
                x = int32(int(x) ^ int(y))
            elif op == BITWISE_AND: 
                x = int32(int32(x) & int(y))
            elif op == LSH: 
                x = int32(int32(x) << (int(y) & 0x1f))
            elif op == URSH: 
                if isFloat(y) or y >= 0xffffffff or y <= -0xffffffff:
                    return int(int(x) & 0xffffffff)
                x = int32((int32(x) & 0xFFFFFFFFL) >> (int(y) & 0x1f))
            elif op == RSH: 
                x = int32(int32(x) >> (int(y) & 0x1f))
            else: 
                self.err(NotImplemented_, "bitwiseOp(): %s" % op)
        except TypeError, e:
            defs.err( "bitwiseOp(): TypeError", str(x), op, str(y), e.message)
            x = 0

        return x

    def assignOp(self, x, y, op):
        #print "assignOp()", x, y, op
        if op in (BITWISE_OR, BITWISE_AND, BITWISE_XOR, 
                        BITWISE_NOT, URSH, RSH, LSH):
            return self.bitwiseOp(x, y, op)
        else:
            return self.arithmOp(x, y, op)

    def funDef(self, f):
        #args = id(self.this) == id(self.globals) and [self.this] or []
        #print "funDef()", id(self.this) == id(self.globals)
        fun = function(self, f)
        if f.functionForm == 0:
            #self.scope[f.name] = fun
            #return self.assign(ustr(f.name), fun, local=True)
            fname = ustr(f.name)
            self.scope[fname] = fun
            return self.scope[fname]
        return fun

    def classDef(self, c):
        cls = buildClass(self, c)
        if c.classForm == 0:
            #return self.assign(ustr(c.name), cls, local=True)
            cname = ustr(c.name)
            self.scope[cname ] = cls
            return self.scope[cname ]
        return cls

    def initVar(self, var, value):
        if id(self) == id(self.root_context):
            self.globals[var] = value
        else:
            self.scope[var] = value

    def while_(self, cond, body):
        while self.compare(cond):
            try: 
                self.exec_(body)
            except BreakOutOfLoops, e: break
            except ContinueLoops, e: 
                self.exec_(cond)
                continue
            except Exception: raise

    def for_(self, setup, cond, update, body):
        self.exec_(setup)
        while self.compare(cond):
            try:
                self.exec_(body)
                self.exec_(update)
            except BreakOutOfLoops, e: break
            except ContinueLoops, e: 
                self.exec_(update)
                continue
            except Exception: raise

    def for_in(self, iterator, object_, body):
        for k, v in object_:
            try:
                self.scope[iterator] = k
                self.exec_(body)
            except BreakOutOfLoops, e: break
            except ContinueLoops, e: continue
            except Exception: raise

    def compare(self, n):
        #print "compare()", n

        t = n.type_
        if t in (GT, LT, EQ, NE, GE, LE, 
                STRICT_EQ, STRICT_NE):
            a = self.exec_(n[0])
            b = self.exec_(n[1])
            # reflect javascript behavior
            #
            if isNaN(a) and isNaN(b):
                return t in (NE, STRICT_NE)
            elif isNull(a) or isNull(b):
                if t in (EQ, STRICT_EQ):
                    return isNull(a) and isNull(b)
                elif t in (NE, STRICT_NE):
                    return not (isNull(a) and isNull(b))
                a = toNumber(a)
                b = toNumber(b)
            elif isObject(a) and isObject(b):
                #print a, b
                if t in (STRICT_EQ, EQ):
                    return id(a) == id(b)
                elif t in (STRICT_NE, NE):
                    return id(a) != id(b)
                else:
                    x = object_prio(a)
                    y = object_prio(b)
                    if (isNumber(a) or isNumber(b) \
                            or isBoolean(a) or isBoolean(b)) and x != y:
                        a = toNumber(a)
                        b = toNumber(b)
                    elif x == y:
                        a = str_(a)
                        b = str_(b)
                    else:
                        a = x
                        b = y
                    #print a, b, x, y
            elif t not in (STRICT_EQ, STRICT_NE):
                if isNumber(a) or isNumber(b) \
                        or isBoolean(a) or isBoolean(b):
                    a = toNumber(a)
                    b = toNumber(b)
                elif isString(a) or isString(b):
                    a = str_(a)
                    b = str_(b)
        else:
            return self.exec_(n)


        if t == GT: return a > b 
        elif t == LT: return a < b 
        elif t == EQ: return a == b 
        elif t == NE: return a != b 
        elif t == GE: return a >= b 
        elif t == LE: return a <= b 
        elif t == STRICT_EQ:
            return a == b and type(a) == type(b)
        elif t == STRICT_NE: 
            return not(a == b) or not type(a) == type(b)

    # JS RegExp converted into Python re expression
    def regexp(self, n):
        return regexp_proto(regexp=n.value['regexp'], modifiers=n.value['modifiers'])

    def undefPropErr(self, prop, n):
        err = "undefined object property %s" % getattr(prop, 'value', prop)
        if self.strict:
            raise JSError, err
        self.warn(err, n)

    def err(self, ex, msg, n=None):
        if n:
            raise ex(msg, n.lineno, n.start, n.end, n.filename, self.stack)
        else:
            raise ex(msg, 0, 0, 0, "", self.stack)

    def warn(self, msg, n):
        sys.stderr.write("WARNING: %s on line %s!\n" % (msg, n.lineno))

# = = = = = = = = = = = = = = = 
#   prototype implementation
# = = = = = = = = = = = = = = = 
class Prototype(JS_Object):
    def __init__(self):
        pass

    # This look for a property in this dictonary or in __proto__
    # if not found. This method will call recursively. 
    def __getattr__(self, k):
        #print "__getattr__", k, k in self.__proto__.__dict__, type(self), type(self.__proto__)
        if k in self.__dict__: return object.__getattr__(self, k)
        elif hasattr(self, "__proto__") and id(getattr(self, "__proto__")) != id(self): 
            return getattr(self.__proto__, k)
        elif k == 'constructor': return None
        elif k == '__proto__': return self
        raise AttributeError, k

    __iter__ = lambda self: object_iter(self)

    def __delattr__(self, k):
        # do nothing if trying to delete native __proto__ property 
        if k == '__proto__' and id(self.__proto__) == id(self): pass
        else:
            JS_Object.__delattr__(self, k)

# Source: http://code.activestate.com/recipes/65212/
def str_base(num, base, numerals = '0123456789abcdefghijklmnopqrstuvwxyz'):
    if base < 2 or base > len(numerals):
        raise ValueError("str_base: base must be between 2 and %i" % len(numerals))

    if num == 0:
        return '0'

    if num < 0:
        sign = '-'
        num = -num
    else:
        sign = ''

    result = ''
    while num:
        result = numerals[num % (base)] + result
        num //= base

    return sign + result

# = = = = = = = = = = = = = = = 
#           numbers
# = = = = = = = = = = = = = = = 
# number prototype
# note: to make it work there is two classes for float and int
class number_proto_(Prototype):
    def __init__(self, x=0):
        Prototype.__init__(self)

    def __getattr__(self, k):
        if k == 'constructor': return number
        elif k == '__proto__': return number_prototype
        else: return Prototype.__getattr__(self, k)

    # convert number intos string with giving base
    toString = publicmethod(lambda this, base=10: str_base(int(this), base))
    __str__ = toString

def number_proto(x):
    if isInt(x):
        return type("<int %s>" % x, (int, number_proto_), {}) (x)
    if isFloat(x):
        return type("<float %s>" % x, (float, number_proto_), {}) (x)

number_prototype = number_proto(0)

#
# Number object
# 
class Number(JS_Function):
    def __init__(self):
        JS_Object.__init__(self)

    prototype = property(lambda self: number_prototype, 
            lambda self, v: None)
    __proto__ = property(lambda self: func_prototype, 
            lambda self, v: None)

    def __newInstance__(self, *args):
        return number_proto(self.__call__(None, *args))

    def __call__(self, this, *args):
        # Number.prototype returns 0 so we should to do this test
        if id(this) == id(self.prototype):
            return self.prototype
        if len(args):
            return toNumber(str_(args[0]))
        return 0
        #type("<" + (len(args) and str(args[0]) or "0") + ">", (number_proto,), {}) 
        
# = = = = = = = = = = = = = = = 
#           strings
# = = = = = = = = = = = = = = = 
# string prototype
class string_proto(str, Prototype):
    def __init__(self, s=""):
        str.__init__(self, s)
        Prototype.__init__(self)
    
    # strings is not allowed setting chars by index
    def __setitem__(self, i, v): 
        if id(self) == id(self.__proto__):
            object.__setattr__(self, i, v)
        else: pass

    def __getitem__(self, i, j=None):
        if j is not None:
            return str.__getitem__(self, slice(i, j))
        else:
            if isNumber(i):
                if i < 0: return undefined
                try:
                    return str.__getitem__(self, i)
                except IndexError, e:
                    return undefined
            else:
                return getattr(self, str_(i))

    def __getattr__(self, k):
        if k == 'length': return len(self)
        elif k == 'constructor': return string
        elif k == '__proto__': return string_prototype
        else: return Prototype.__getattr__(self, k)

    toString = publicmethod(lambda this: str(this))

    @publicmethod
    def substr(self, start=None, n=None):
        """Returns the characters in a string beginning at the specified location through the specified number of characters."""
        #print "substr()", self, start, n
        s = str_(self)
        if start == None and n == None: return s
        else:
            if start == None: start = 0
            else: start = toNumber(start)
            if n == None: end = len(s) 
            else: end = toNumber(n)
            if end < 0: return ''
            if start > 0 and end < 0 and n != None: return ''
            if end > len(s): end = len(s)
            return s[start:start+end]

    @publicmethod
    def split(this, sep=None):
        """Splits a String object into an array of strings by separating the string into substrings."""
        return array_proto(*str(this).split(sep))

    @publicmethod
    def toLowerCase(self):
        """
        Returns the calling string value converted to lower case.
        """
        return self.lower()

    @publicmethod
    def replace(this, regexp, subs):
        """
        Used to find a match between a regular expression and a string, and to replace the matched substring with a new substring.
        """
        # replace $x with \x
        # TODO need to escape \x in subs
        subs = re.sub(r'\$(\d+)', r"\\\g<1>", subs)
        # Python will raise error if i increase counter inside function
        t = {"i":0, "g":regexp.global_}
        # FIXME rude hack
        def repl(m): 
            if not t["g"] and t["i"]>0: return m.group(0)
            t["i"]+=1
            return re.sub(regexp.regexp, subs, m.group(0))
        return re.sub(regexp.regexp, repl, str(this))

    @publicmethod
    def match(this, regexp):
        """
        Used to match a regular expression against a string.
        """
        if regexp.global_:
            l = re.findall(regexp.regexp, str(this))
            return len(l) and array_proto(*l) or null
        else:
            m = re.search(regexp.regexp, str(this))
            if not m: return null
            groups = m.groups()
            if len(groups):
                l = (m.string[m.start():m.end()],) + groups
            else:
                l = []
                i = 0
                try:
                    while m.group(i):
                        l.append(m.group(i))
                        i += 1
                except IndexError: pass
            return array_proto(*l)

    """
    charAt
        Returns the character at the specified index.
    charCodeAt
        Returns a number indicating the Unicode value of the character at the given index.
    concat
        Combines the text of two strings and returns a new string.
    indexOf
        Returns the index within the calling String object of the first occurrence of the specified value, or -1 if not found.
    lastIndexOf
        Returns the index within the calling String object of the last occurrence of the specified value, or -1 if not found.
    localeCompare
        Returns a number indicating whether a reference string comes before or after or is the same as the given string in sort order.
    match
    quote
        Non-standard
        Wraps the string in double quotes ('"').
    search
        Executes the search for a match between a regular expression and a specified string.
    slice
        Extracts a section of a string and returns a new string.
    substr
        Returns the characters in a string beginning at the specified location through the specified number of characters.
    substring
        Returns the characters in a string between two indexes into the string.
    toLocaleLowerCase
        The characters within a string are converted to lower case while respecting the current locale. For most languages, this will return the same as toLowerCase.
    toLocaleUpperCase
        The characters within a string are converted to upper case while respecting the current locale. For most languages, this will return the same as toUpperCase.
    toSource
        Non-standard
        Returns an object literal representing the specified object; you can use this value to create a new object. Overrides the Object.toSource method.
    toString
        Returns a string representing the specified object. Overrides the Object.toString method.
    toUpperCase
        Returns the calling string value converted to uppercase.
    trim
        New in Firefox 3.5 Non-standard
        Trims whitespace from the beginning and end of the string.
    trimLeft
        New in Firefox 3.5 Non-standard
        Trims whitespace from the left side of the string.
    trimRight
        New in Firefox 3.5 Non-standard
        Trims whitespace from the right side of the string.
    """

string_prototype = string_proto()

#
# String object
#
class String(JS_Function):
    def __init__(self, s=''):
        str.__init__(self)
        #self.prototype.constructor = self
        
    prototype = property(lambda self: string_prototype, 
            lambda self, v: None)
    __proto__ = property(lambda self: func_prototype, 
            lambda self, v: None)

    def __newInstance__(self, *args):
        return string_proto(self.__call__(None, *args))

    def __call__(self, this, *args):
        if id(this) == id(self.prototype):
            return self.prototype
        if len(args):
            return str_(args[0])
        return str_("")

# = = = = = = = = = = = = = = = 
#           boolean
# = = = = = = = = = = = = = = = 
# boolean prototype
# note: bool class cannot be extended so boolean type is emulated
class bool_proto(int, Prototype):
    #__isbool__ = True
    def __init__(self, x=0):
        int.__init__(self, int(x))
        Prototype.__init__(self)

    def __getattr__(self, k):
        if k == 'constructor': return boolean
        elif k == '__proto__': return bool_prototype
        elif k == '__isbool__': return True
        else: return Prototype.__getattr__(self, k)

bool_prototype = bool_proto()

#
# Boolean object
#
class Boolean(JS_Function):
    def __init__(self):
        JS_Object.__init__(self)
        #self.prototype.constructor = self

    prototype = property(lambda self: bool_prototype, 
            lambda self, v: None)
    __proto__ = property(lambda self: func_prototype, 
            lambda self, v: None)

    def __newInstance__(self, *args):
        return bool_proto(self.__call__(None, *args))

    def __call__(self, this, *args):
        if id(this) == id(self.prototype):
            return self.prototype
        if len(args):
            return bool(args[0])
        return false

# = = = = = = = = = = = = = = = 
#            object
# = = = = = = = = = = = = = = = 
# object prototype
class object_proto(Prototype):
    def __init__(self, **kwargs):
        Prototype.__init__(self)
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def __getattr__(self, k):
        if k == 'constructor': return object_
        elif k == '__proto__': return object_prototype
        else: return Prototype.__getattr__(self, k)

    toString = publicmethod(lambda *args: "[object Object]")
    __str__ = toString

object_prototype = object_proto()

#
# Object
#
class Object(JS_Function):
    def __init__(self):
        JS_Object.__init__(self)
        #self.prototype.constructor = self

    prototype = property(lambda self: object_prototype, 
            lambda self, v: None)
    __proto__ = property(lambda self: func_prototype, 
            lambda self, v: None)

    def __newInstance__(self, *args):
        return self.__call__(None, *args)

    def __call__(self, this, *args):
        if len(args):
            t = args[0]
            if isString(t): return string.__newInstance__(t)
            elif isNumber(t): 
                return number.__newInstance__(t)
            elif isBoolean(t): 
                return boolean.__newInstance__(t)
            else: 
                return args[0]
        return object_proto()

# = = = = = = = = = = = = = = = 
#            array
# = = = = = = = = = = = = = = = 
# array prototype
class array_proto(list, Prototype):
    def __init__(self, *args):
        list.__init__(self, args)
        Prototype.__init__(self)

    # Setting an item of list and extend it if neccesary
    def __setitem__(self, i, value):
        #if id(self.__proto__) == id(self):
            #prototype.__setitem__(self, i, value)
        if isNull(i): index = "null"
        elif isUndefined(i): index = "undefined"
        else: index = toNumber(i)
        if isInt(index) and index >= 0:
            if index > len(self)-1:
                arr = list(self)
                list.__setitem__(self, slice(0, index + 1), [None] * (index + 1))
                list.__setitem__(self, slice(0, len(arr)), arr)
            list.__setitem__(self, index, value)
        else:
            setattr(self, str_(i), value)

    def __getitem__(self, i):
        #if id(self.__proto__) == id(self):
            #prototype.__getitem__(self, i)
        if isNull(i): index = "null"
        elif isUndefined(i): index = "undefined"
        else: index = toNumber(i)
        if isInt(index) and index >= 0:
            if index >= len(self):
                # reflected JS behavior, get value of prototype
                return list.__getitem__(self.__proto__, index)
            return list.__getitem__(self, index)
        return getattr(self, str_(i))

    def __getattr__(self, k):
        if k == 'length': return len(self)
        elif k == 'constructor': return array
        elif k == '__proto__': return array_prototype
        else: return Prototype.__getattr__(self, k)

    @publicmethod
    def push(self, x): 
        list.append(self, x)
        return x

    @publicmethod
    def pop(self): return list.pop(self)

    @publicmethod
    def slice(this, s=0, i=None): 
        if i == None: i = len(this)
        return array_proto(*this[s:i])

    @publicmethod
    def join(this, s=","): 
        l = []
        i = 0
        while i<this.length:
            l.append(str(this[i]))
            i += 1
        return string_proto(s.join(l))

    __iter__ = lambda self: array_iter(self)
    """
    if id(self.__proto__) == id(self):
        return object_iter(self)
    return list.__iter__(self)
    """

    __str__ = lambda self: ",".join([str_(x)
                  for x in list.__iter__(self)])

array_prototype = array_proto()

def array_iter(arr):
    collect = list()
    i = 0
    for x in list.__iter__(arr):
        collect.append((str(i), x))
        i+=1
    collect.extend(arr.__dict__.items())
    for k, v in collect:
        yield (k, v)

#
# Array
#
class Array(JS_Function): 
    def __init__(self):
        JS_Object.__init__(self)
        #self.prototype.constructor = self

    prototype = property(lambda self: array_prototype, 
            lambda self, v: None)
    __proto__ = property(lambda self: func_prototype, 
            lambda self, v: None)

    def __getattr__(self, k):
        if k == 'constructor': return array
        elif k == '__proto__': return array_prototype
        else: Prototype.__getattr__(self, k)

    def __newInstance__(self, *args):
        return self.__call__(None, *args)

    def __call__(self, this, *args):
        if id(this) == id(self.prototype):
            return self.prototype
        if len(args):
            if len(args) == 1:
                if isNumber(args[0]):
                    if args[0] < 0 or isNaN(args[0]) or \
                            isInfinity(args[0]) or isFloat(args[0]): 
                        raise RangeError_, "Invalid array length"
                    _args = [None] * args[0]
                    return array_proto(*_args)
                else:
                    return array_proto(*args)
            else:
                return array_proto(*args)
        else:
            return array_proto()

# = = = = = = = = = = = = = = = 
#           function
# = = = = = = = = = = = = = = = 
# function prototype
# Note: constructor return some object or class instance
class func_proto(Prototype):
    def __init__(self):
        Prototype.__init__(self)

    def __getattr__(self, k):
        #print "func_proto.__getattr__", k
        if k == 'constructor': return function_
        elif k == '__proto__': return func_prototype
        else: return Prototype.__getattr__(self, k)

    @publicmethod
    def call(this, context=None, *args):
        return this.constructor(context, *args)

    @publicmethod
    def apply(this, context=None, *args):
        return func_proto.call(this, context, *args[0])

    def __call__(self, context, *args):
        return self.constructor(context, *args)

    def __newInstance__(self, *args):
        instance = Prototype()
        instance.__proto__ = self.prototype
        instance.constructor = self.constructor
        obj = instance.constructor(instance, *args)
        if isObject(obj): return obj
        return instance 

    @publicmethod
    def toString(this, *args):
        return this.constructor.toString(this)

    __str__ = lambda self: self.toString(self)
                                
func_prototype = func_proto()

class arguments(tuple):
    length = property(lambda self: len(self))

# function  constructor
#
def function(parent, f):
    params = f.params
    body = f.body
    name = getattr(f, 'name', None)
    def constructor(context, *args):
        #print "constructor()", context, args
        #print "call %s(), # %s" % (name, f.lineno)
        returnValue = undefined
        # initialize new context
        ctx = JS_Context(parent=parent, caller=fun)
        ctx.scope['arguments'] = arguments(args)
        ctx.context = context
        for i in range(len(params)):
            if i < len(args):
                ctx.scope[params[i]] = ctx.scope['arguments'][i]
            else:
                ctx.scope[params[i]] = undefined
        try:
            returnValue = ctx.exec_(body)
        except BreakOutOfLoops: 
            returnValue = ctx.returnValue
        
        return returnValue

    constructor.__name__ = ustr(getattr(f, "name", 'anonymous'))
    constructor.toString = lambda this, *args:  \
        "function %s(%s) %s" % (
            constructor.__name__, 
            ",".join([p for p in f.params]),
            "{/*stub*/}") 

    init = dict(
        constructor = staticmethod(constructor),
        prototype = object_proto(),
        caller = None
    )
    fun = type(ustr(getattr(f, "name", 'empty')), (func_proto,), init) ()
    return fun

#
# Function
#
class Function(JS_Function):
    def __init__(self, root_context):
        JS_Object.__init__(self)
        self.root_context = root_context
        #self.prototype.constructor = self

    prototype = property(lambda self: func_prototype, 
            lambda self, v: None)
    __proto__ = property(lambda self: func_prototype, 
            lambda self, v: None)

    anonymous = jsparser.parse("function anonymous(){}")[0]

    def __call__(self, this, *args):
        if len(args):
            f = JS_Function(
                name = "anonymous",
                params = args[:-1],
                body = jsparser.Script(lexer.Tokenizer(args[-1]), true)
            )
            return function(self.root_context, f)
        else:
            return function(self.root_context, self.anonymous)

    def __newInstance__(self, *args):
        return self.__call__(None, *args)

# regexp prototype
class regexp_proto(Prototype):
    def __init__(self, **kwargs):
        Prototype.__init__(self)

        self.global_ = False
        self.multiline = False
        self.ignorecase = False
        self.flags = 0

        if 'regexp' in kwargs:
            modifiers = kwargs.get("modifiers") or ""
            if "m" in modifiers: 
                self.flags |= re.MULTILINE
                self.multiline = True
            if "i" in modifiers: 
                self.flags |= re.IGNORECASE
                self.ignorecase = True
            if "g" in modifiers: 
                self.global_ = True
            #print kwargs['regexp'], modifiers, self.flags, self.global_
            self.regexp = re.compile(kwargs['regexp'], self.flags)

    def __getattr__(self, k):
        if k == 'constructor': return regexp
        elif k == '__proto__': return regexp_prototype
        else: return prototype.__getattr__(self, k)

    __str__ = lambda self: "[object Object]"

regexp_prototype = regexp_proto()

# RegExp
class RegExp(JS_Function):
    def __init__(self):
        JS_Function.__init__(self)

    def __newInstance__(self, this, regexp={}, modifiers=None):
        return regexp_proto(regexp=regexp, modifiers=modifiers)

    def __call__(self, this, *args):
        return self.__newInstance__(*args)

#
# Math object
#
class Math(JS_Object):
    def __init__(self): 
        JS_Object.__init__(self)

    #native = JS_Object.native + ["PI", "E", "LN2", "LN10", "LN2E", "LN10E",
        #"SQRT2", "SQRT1_2", "sqrt", "abs", "sin", "cos", "tan",
        #"acos", "asin", "atan", "atan2", "ceil", "ext", "floor",
        #"log", "max", "min", "pow", "random", "round"]

    # Pi value
    PI = property(lambda self: self.number(math.pi))

    # The constant of E, the base of natural logarithms.
    E = property(lambda self: math.e)

    # The natural logarithm of 2.
    LN2 = property(lambda self: math.log(2))

    # The natural logarithm of 10.
    LN10 = property(lambda self: math.log(10))

    # Base 2 logarithm of E.
    LN2E = property(lambda self: math.log(math.e, 2))

    # Base 10 logarithm of E.
    LN10E = property(lambda self: math.log(math.e, 10))

    # Square root of 1/2.
    SQRT1_2 = property(lambda self: math.sqrt(1/2))

    # Square root of 2.
    SQRT2 = property(lambda self: math.sqrt(2))

    # Returns the square root of x.
    sqrt = publicmethod(lambda this, x: math.sqrt(x))

    # Returns the Sin of x, where x is in radians.
    sin = publicmethod(lambda this, x: math.sin(x))

    # Returns absolute value of x.
    abs = publicmethod(lambda this, x: abs(x))

    # round(x) 	Rounds x up or down to the nearest integer. It rounds .5 up. Example(s).
    round = publicmethod(lambda this, x: round(x))

    # random() 	Returns a pseudorandom number between 0 and 1.
    random = publicmethod(lambda this: random.random())

    """
    cos(x) 	Returns cosine of x, where x is in radians.
    tan(x) 	Returns the Tan of x, where x is in radians.
    acos(x) 	Returns arc cosine of x in radians.
    asin(x) 	Returns arc sine of x in radians.
    atan(x) 	Returns arc tan of x in radians.
    atan2(y, x) 	Counterclockwise angle between x axis and point (x,y).
    ceil(x) 	Returns the smallest integer greater than or equal to x. (round up).
    exp(x) 	Returns ex
    floor(x) 	Returns the largest integer less than or equal to x. (round down)
    log(x) 	Returns the natural logarithm (base E) of x.
    max(a, b) 	Returns the larger of a and b.
    min(a, b) 	Returns the lesser of a and b.
    pow(x, y) 	Returns X^y
    """

    __repr__ = lambda self: "Math"

#
# Date
#
class Date(JS_Object):
    def __init__(self):
        JS_Object.__init__(self)
    
    def __str__(self): return "<date>"

number = Number()
string = String()
boolean = Boolean()
function_ = Function(None)
array = Array()
object_ = Object()
regexp = RegExp()

#
# Global object
#
class Globals(JS_Object):
    def __init__(self): pass

#
# Main PyJS class
#
class PyJS(JS_Context):
    def __init__(self):
        self.globals = Globals()
        # Hidden read-only global objects
        self.js_objects = dict(
            # global methods
            parseInt = lambda this, x: lexer.parseInt(x),
            parseFloat = lambda this, x: lexer.parseFloat(x),
            isNaN = lambda this, x: isNaN(toNumber(x)),

            # JS base objects
            Number = number,
            String = string,
            Boolean = boolean,
            Array = array,
            Object = object_,
            Function = Function(self),
            RegExp = regexp,
            Math = Math(),

            # Exceptions,
            #JSError = JSError(),

            # ECMAScript exceptions,
            Error = ECMAScriptError(),
            ReferenceError = ReferenceError(),
            TypeError = TypeError_(),
            SyntaxError = SyntaxError_(),
            RangeError = RangeError_(),
            URIError = URIError(),
        )

        JS_Context.__init__(self, context=self.globals, scope=self.globals)
        setattr(self.globals, "load", lambda this, *args: self.load_(*args))
        setattr(self.globals, "print", lambda this, *args: self.print_(*args))
        setattr(self.globals, "eval",  lambda this, s: self.eval_(s))

    # safe eval
    def eval_(self, s):
        n = jsparser.parse(s)
        return self.root_context.exec_(n)
    
    # safe load
    # TODO load script from current dir for script
    def load_(self, *args):
        for path in args:
            filename = os.path.split(path)[1]
            n = jsparser.parse(file(filename, 'r').read())
            self.root_context.exec_(n)

    def print_(self, *args):
        print (" ".join([str(s) for s in args]))
