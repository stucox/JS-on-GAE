#!/usr/bin/env python

"""
 Converts a Pyjon parse tree into JavaScript syntax.

 Original code by JT Olds, 2009
 Updated in Jan 2011 by Evgen Burzak <buzzilo@gmail.com>
"""

__author__ = "JT Olds"
__author_email__ = "jtolds@xnet5.com"
__date__ = "2009-03-24"

__author__ = "Burzak"
__author_email__ = "buzzilo@gmail.com"
__date__ = "2009-03-24"

__all__ = ["convert", "UnknownNode", "OtherError", "ProgrammerError", "Error_"]

class Error_(Exception): pass
class UnknownNode(Error_): pass
class OtherError(Error_): pass
class ProgrammerError(OtherError): pass

import sys
import defs, jsparser

js = jsparser

class NodeToJS(): 

    def __init__(self, parent=None): 
        if parent:
            self.stack=parent.stack
        else:
            self.stack=[]

        self.had_error = False

    preserve_comments = False
    preserve_whitespaces = False
    newline = "\n"
    semicolon = ";"
    tab = "  "

    def convert(self, n, i, c, handledattrs=[]):
        self.stack.append(dict(
            node = n.type,
            attrs = dict([[attr, True] for attr in handledattrs]),
            subnodes = [],
        ))
        try:
            self.check(n, attrs=["append", "count", "extend", "filename", "getSource",
                                 "indentLevel", "index", "insert", "lineno", "pop",
                                 "remove", "reverse", "sort", "tokenizer", "type", "type_",
                                 "commentBefore", "whitespaces"],
                          optattrs=["end", "start", "value", "labels", 
                                    "assignWhitespace","parenthesized"])

            convert_type = "convert_" + n.type.lower()
        
            if callable(getattr(self, convert_type, None)):
                commentBefore = self.preserve_comments and n.commentBefore or ""
                whitespaces = self.preserve_whitespaces and n.whitespaces or ""
                if self.preserve_whitespaces: 
                    # for assign node whitespaces will duplicated, quick fix here 
                    if n.type == "ASSIGN": whitespaces = ""
                else: 
                    n.whitespaces = ""

                if getattr(n, "parenthesized", False): t = "(%s)"
                else: t = "%s"

                return t % (commentBefore + whitespaces + getattr(self, convert_type)(n,i,c))

            else:
                raise UnknownNode, "Unknown type %s" % n.type

        except AssertionError, e:
            self.had_error = True
            raise OtherError("%s\nAssertion error in node %s on line %s" % (e, n.type,
                    getattr(n, "lineno", None)))

        except Exception, e:
            self.had_error = True
            raise OtherError("%s\nException in node %s on line %s" % (e, n.type,
                    getattr(n, "lineno", None)))
        finally:
            if not self.had_error:
                current = self.stack.pop()
                realkeys = [x for x in dir(n) if x[:2] != "__"]
                for key in realkeys:
                    if key not in current['attrs']:
                        raise ProgrammerError, "key '%s' unchecked on node %s!" % (
                                key, n.type)
                if len(realkeys) != len(current['attrs']):
                    for key in current['attrs']:
                        if key not in realkeys:
                            raise ProgrammerError, ("key '%s' checked "
                                    "unnecessarily on node %s!" % (key, n.type))
                if len(current['subnodes']) != len(n):
                    raise ProgrammerError, ("%d subnodes out of %d checked on node "
                            "%s" % (len(current['subnodes']), len(n), n.type))

    # short link for convert()
    o = convert

    def check(self, n, attrs=[], optattrs=[], subnodes=0):
        current = self.stack[-1]
        if not (type(attrs) == list and type(optattrs) == list and
                type(subnodes) == int):
            raise ProgrammerError, "Wrong arguments to check(...)!"
        for attr in attrs: current['attrs'][attr] = True
        for attr in optattrs:
            if hasattr(n, attr): current['attrs'][attr] = True
        for i in xrange(subnodes):
            current['subnodes'].append(True)
        return True

    # FIXME
    def props():
        if c["include_props"]:
            props_to_include = [x for x in ("lineno", "start", "end",
                    "readOnly") if hasattr(n, x)]
            if len(props_to_include) > 0:
                s = " (@"
                for prop in props_to_include:
                    s += " (%s %s)" % (prop.upper(), getattr(n, prop))
                return s +")"
        return ""

    def convert_function(self,n,i,c):
        self.check(n,attrs=["functionForm","params","body"], optattrs=["name"])
        funName = getattr(n, "name", "")
        if n.functionForm == js.DECLARED_FORM:
            return "function %s(%s) %s" % (funName,
                    ", ".join(param for param in n.params),
                    self.o(n.body,i,c))
        else:
            return "function %s(%s)%s" % (funName, ",".join(n.params), self.o(n.body,i,c))
        

    def convert_index(self,n,i,c):
        self.check(n,subnodes=2)
        return "%s[%s]" % (self.o(n[0],i,c), self.o(n[1],i,c))

    def convert_var(self,n,i,c):
        self.check(n,subnodes=len(n),optattrs=["destructurings"])
        return "%s %s" % (n.value.lower(), ",".join((self.o(x,i,c) for x in n)))

    def convert_header(self,n,i,c):
        return "%s\n" % n.value

    def convert_script(self,n,i,c,optattrs=[]):
        self.check(n,attrs=["funDecls","varDecls","expDecls","modDecls",
                    "impDecls","loadDeps","hasEmptyReturn","hasReturnWithValue",
                    "isGenerator","isRootNode"], 
                    optattrs=["endWhitespaces"] + optattrs,
                    subnodes=len(n))
        #  sys.stderr.write("WARNING: skipping funDecls and varDecls\n")
        if self.preserve_whitespaces: 
            ws = ""
            end_ws = getattr(n, "endWhitespaces", "")
        else: 
            ws = self.tab
            end_ws = self.newline + i[:-2]
        if len(n)>0:
            return "{" + (ws and self.newline) + i + \
                        ((ws and self.newline+i).join((
                            "%s%s" % (self.o(x,i+ws,c), self.semicolon) for x in n))) \
                        + "%s}" % end_ws
        else:
            return "{}"

    def convert_assign(self,n,i,c):
        self.check(n,attrs=["assignOp"],subnodes=2)
        s = self.o(n[0], i, c)
        ws = self.preserve_whitespaces and n.whitespaces or ""
        if getattr(n, "assignOp", None):
            s += "%s=" % defs.tokens[n.assignOp]
        else:
            s += "="
        return s + self.o(n[1], i, c)

    # actually semicolon will be appended in block and script node
    def convert_semicolon(self,n,i,c):
        self.check(n, attrs=["expression"])
        if not n.expression: return ""
        return self.o(n.expression, i, c)

    def convert_array_init(self, n, i, c):
        self.check(n,subnodes=len(n))
        a = []
        for x in n:
            if x is not None:
                a.append( self.o(x,i,c) )
            else:
                a.append( "" )
        return "[%s]" % ",".join(a) 

    def convert_block(self, n, i, c):
        self.check(n,subnodes=len(n),attrs=["varDecls"], 
                        optattrs=["endWhitespaces"])
        if self.preserve_whitespaces: 
            ws = ""
            end_ws = getattr(n, "endWhitespaces", "")
        else: 
            ws = self.tab
            end_ws = self.newline + i[:-2]
        if len(n) > 0:
            return ("{" + (ws and self.newline) + i + \
                    ((ws and self.newline)+i).join(("%s%s" % (self.o(x,i+ws,c), self.semicolon) 
                                                    for x in n)) + 
                    "%s}" % end_ws)
        return "{}"

    def convert_continue(self, n, i, c): 
        self.check(n,attrs=["target"], optattrs=["label"])
        if hasattr(n,"label"):
            return "%s %s%s" % (n.value.lower(), n.label, self.semicolon)
        return "%s%s" % (n.value.lower(), self.semicolon)

    convert_break = convert_continue

    def convert_call(self, n, i, c):
        self.check(n,subnodes=2)
        return "%s(%s)" % (self.o(n[0], i, c), self.o(n[1], i, c))

    def convert_case(self, n, i, c):
        self.check(n,attrs=["caseLabel","statements"])
        return "case %s: %s" % (self.o(n.caseLabel,i,c), self.o(n.statements,i+"  ",c))

    def convert_catch(self, n, i, c):
        self.check(n,attrs=["block","varName"],optattrs=["guard"])
        #if n.guard is not None:
            #return "(GUARDED-CATCH%s %s %s %s)" % (props(), n.varName,
                    #self.o(n.guard,i,c), self.o(n.block,i,c))
        return "catch (%s) %s" % (n.varName, self.o(n.block,i,c))

    def convert_comma(self, n, i, c):
        self.check(n,subnodes=len(n))
        return ','.join(self.o(x, i, c) for x in n)

    convert_list = convert_comma

    def convert_debugger(self, n, i, c):
        return "(DEBUGGER%s)" % props()

    def convert_default(self, n, i, c):
        self.check(n,attrs=["statements"])
        return "default : %s" % (self.o(n.statements,i+"  ",c))

    def convert_delete(self, n, i, c):
        self.check(n,subnodes=1)
        return "%s %s" % (n.value, self.o(n[0],i,c))

    convert_typeof = \
    convert_new = \
    convert_unary_minus = \
    convert_not = \
    convert_void = \
    convert_bitwise_not = \
    convert_unary_plus = convert_delete

    def convert_do(self, n, i, c):
        self.check(n,attrs=["body", "condition", "isLoop"])
        assert n.isLoop
        return "do %s while (%s) " % (self.o(n.body,i,c), self.o(n.condition,i,c))

    def convert_dot(self, n, i, c):
        self.check(n,subnodes=2)
        return "%s.%s" % (self.o(n[0],i,c), self.o(n[1],i,c))

    def convert_for(self, n, i, c):
        self.check(n,attrs=["body","setup","condition","update","isLoop"])
        assert n.isLoop
        if n.setup is not None: setup = self.o(n.setup,i,c)
        else: setup = ""
        if n.condition is not None: condition = self.o(n.condition,i,c)
        else: condition = ""
        if n.update is not None: update = self.o(n.update,i,c)
        else: update = ""
        if n.body is not None: body = self.o(n.body,i,c)
        else: body = ""

        return "for (%s) %s" % (self.semicolon.join((setup, condition, update)), body)

    def convert_for_in(self, n, i, c):
        self.check(n,attrs=["body","iterator","object","isLoop"],optattrs=["varDecl"])
        assert n.isLoop
        s = "for "
        object = self.o(n.object,i,c)
        body = self.o(n.body,i,c)
        if getattr(n, "varDecl", None) :
            assert n.varDecl.type == "VAR"
            assert len(n.varDecl) == 1
            assert n.varDecl[0].type == "IDENTIFIER"
            assert n.varDecl[0].value == n.iterator.value
            iterator = "%s %s" % (n.varDecl.type.lower(), self.o(n.iterator,i,c))
        else:
            iterator = n.iterator.value

        return s + "(%s in %s) %s" % (iterator, object, body)

    def convert_group(self, n, i, c):
        self.check(n,subnodes=1)
        return "(%s)" % self.o(n[0],i,c)

    def convert_hook(self, n, i, c):
        self.check(n,subnodes=3)
        return "%s ? %s : %s" % (self.o(n[0],i,c), self.o(n[1],i,c), self.o(n[2],i,c))

    def convert_identifier(self, n, i, c):
        self.check(n,optattrs=["initializer","name","readOnly","assignWhitespace"])
#            if getattr(n,"readOnly",False): assert hasattr(n,"initializer")
        if self.preserve_whitespaces: ws = getattr(n, "assignWhitespace", " ")
        else: ws = ""
        if hasattr(n,"name"): assert n.name == n.value
        if hasattr(n,"initializer"):
            return "%s%s=%s" % (n.value, ws, self.o(n.initializer, i, c))
        return str(n.value)

    def convert_if(self, n, i, c):
        self.check(n,attrs=["condition","thenPart","elsePart","labels"])

        else_ws = self.newline + i[0:-2]
        if n.elsePart:
            if self.preserve_whitespaces and self.preserve_comments:
                else_ws = n.elsePart.commentBefore + n.elsePart.whitespaces
                n.elsePart.commentBefore = n.elsePart.whitespaces = ""

            return "if (%s) %s %selse %s" % (
                    self.o(n.condition,i,c), self.o(n.thenPart,i,c), else_ws,
                    self.o(n.elsePart, i, c))
        return "if (%s) %s" % (self.o(n.condition,i,c), self.o(n.thenPart, i,c))

    def convert_increment(self, n, i, c):
        self.check(n,optattrs=["postfix"], subnodes=1)
        if getattr(n, "postfix", False):
            return "%s%s" % (self.o(n[0], i, c), n.value)
        return "%s%s" % (n.value, self.o(n[0], i, c))

    convert_decrement = convert_increment

    def convert_label(self, n, i, c):
        self.check(n,attrs=["label","statement"])
        return "%s:\n%s%s" % (n.label, i,
                self.o(n.statement, i+"  ", c))

    def convert_new_with_args(self, n, i, c):
        self.check(n,subnodes=2)
        return "%s %s (%s)" % (n.value.lower(), self.o(n[0],i,c), self.o(n[1],i,c))

    def convert_number(self, n, i, c):
        self.check(n,attrs=["integer"], optattrs=["isHex"])
        if n.integer and n.isHex:
            return hex(n.value)
        else:
            return str(n.value)

    def convert_true(self, n, i, c):
        return str(n.value).lower()

    convert_undefined = \
    convert_false = \
    convert_this = \
    convert_null = convert_true

    def convert_object_init(self, n, i, c):
        self.check(n,subnodes=len(n))
        if len(n) > 0:
            return "{%s}" % (",").join('%r:%s' % (self.o(x[0],i,c), self.o(x[1],i,c)) for x in n)
        return "{}"

    def convert_plus(self, n, i, c):
        self.check(n,subnodes=2)
        return "%s %s %s" % (self.o(n[0],i,c), n.value, self.o(n[1],i,c))

    convert_lt = \
    convert_eq = \
    convert_and = \
    convert_or = \
    convert_minus = \
    convert_mul = \
    convert_le = \
    convert_ne = \
    convert_strict_eq = \
    convert_div = \
    convert_ge = \
    convert_instanceof = \
    convert_in = \
    convert_gt = \
    convert_bitwise_or = \
    convert_bitwise_and = \
    convert_bitwise_xor = \
    convert_strict_ne = \
    convert_lsh = \
    convert_rsh = \
    convert_ursh = \
    convert_mod = convert_plus

    def convert_property_init(self, n, i, c):
        self.check(n,subnodes=2)
        return "%s:%s" % (self.o(n[0],i,c), self.o(n[1],i,c))

    def convert_regexp(self, n, i, c):
        return "/%s/%s" % (n.value["regexp"], n.value["modifiers"])

    def convert_return(self, n, i, c):
        if n.value == None:
            return "return"
            #return "return (%r)" % (n.value)
        else:
            return "return %s" % self.o(n.value, i, c)

    def convert_string(self, n, i, c):
        return repr(n.value)

    def convert_switch(self, n, i, c):
        self.check(n,attrs=["cases", "defaultIndex", "discriminant"])
        assert (n.defaultIndex == -1 or
                n.cases[n.defaultIndex].type == "DEFAULT")
        return "switch (%s) {\n%s%s}" % (self.o(n.discriminant,i,c), i,
                ("\n"+i).join(self.o(x,i,c) for x in n.cases))

    def convert_throw(self, n, i, c):
        self.check(n,attrs=["exception"])
        return "throw %s" % (self.o(n.exception,i,c))

    def convert_try(self, n, i, c):
        self.check(n,attrs=["catchClauses","tryBlock"], optattrs=["finallyBlock"])
        if hasattr(n,"finallyBlock"):
            return "try \n  " + i + ("\n  "+i).join(
                    [self.o(n.tryBlock,i+"  ",c)] + 
                    [self.o(x,i+"  ",c) for x in n.catchClauses] + \
                    [self.o(n.finallyBlock,i+"  ",c)])
        return "try " + ("\n"+i[:-2]).join(
                [self.o(n.tryBlock,i,c)] + [self.o(x,i,c)
                for x in n.catchClauses])

    def convert_with(self, n, i, c):
        self.check(n,attrs=["body", "object"])
        defs.err("WARNING: A bad person wrote the code being "
                        "parsed. Don't use 'with'!")
        return "with (%s) %s" % (self.o(n.object,i,c), self.o(n.body,i,c))

    def convert_while(self, n, i, c):
        self.check(n,attrs=["condition","body","isLoop"])
        assert n.isLoop
        return "while (%s) %s" % (self.o(n.condition,i,c), self.o(n.body, i,c))


def convert(parsetree, include_props=False):
    """Takes a PyNarcissus parse tree and returns a string of S-expressions

    Args:
        parsetree: the PyNarcissus parse tree
        include_props: if true, the s-expressions have additional information
            included via @ attribute expressions, such as line-number.
    Returns:
        string
    Raises:
        UnknownNode: if a node hasn't been properly accounted for in the
            conversion
        ProgrammerError: if the conversion routine wasn't written with the best
            understanding of the parse tree
        OtherError: if some other error happened we didn't understand.
    """

    js = NodeToJS()
    return js.convert(parsetree, "", {}) + "\n"

