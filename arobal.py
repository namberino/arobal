from string_format import *
import string
import os
import math

DIGITS = "0123456789"
LETTERS = string.ascii_letters
LETTERS_DIGITS = LETTERS + DIGITS

KEYWORDS = [
    "var",
    "and",
    "or",
    "not",
    "if",
    "elif",
    "else",
    "then",
    "for",
    "to",
    "step",
    "while",
    "function",
    "end"
]

# Token types
TT_INT = "INT"
TT_FLOAT = "FLOAT"
TT_STRING = "STRING"
TT_PLUS = "PLUS"
TT_MINUS = "MINUS"
TT_MUL = "MUL"
TT_DIV = "DIV"
TT_POW = "POW"
TT_LPAREN = "LPAREN"
TT_RPAREN = "RPAREN"
TT_LSQUARE = "LSQUARE" # [
TT_RSQUARE = "RSQUARE" # ]
TT_EQUAL = "EQ"
TT_EE = "EE" # ==
TT_NE = "NE" # !=
TT_LT = "LT" # <
TT_GT = "GT" # >
TT_LTE = "LTE" # <=
TT_GTE = "GTE" # >=
TT_IDENTIFIER = "IDENTIFIER"
TT_KEYWORD = "KEYWORD"
TT_COMMA = "COMMA"
TT_ARROW = "ARROW"
TT_NEWLINE = "NEWLINE"
TT_EOF = "EOF"

class Error:
    def __init__(self, pos_start, pos_end, err_name, details) -> None:
        self.err_name = err_name
        self.details = details
        self.pos_start = pos_start
        self.pos_end = pos_end

    def as_string(self):
        result = f"{self.err_name}: {self.details}"
        result += f"\nFile {self.pos_start.file_name}, line {self.pos_start.line + 1}"
        result += f"\n{strings_with_arrows(self.pos_start.file_text, self.pos_start, self.pos_end)}"

        return result

class IllegalCharacterError(Error):
    def __init__(self, pos_start, pos_end, details) -> None:
        super().__init__(pos_start, pos_end, "Illegal Character", details)

class ExpectedCharError(Error):
	def __init__(self, pos_start, pos_end, details):
		super().__init__(pos_start, pos_end, 'Expected Character', details)

class InvalidSyntaxError(Error):
    def __init__(self, pos_start, pos_end, details) -> None:
        super().__init__(pos_start, pos_end, "Invalid Syntax", details)

class RuntimeError(Error):
    def __init__(self, pos_start, pos_end, details, context) -> None:
        super().__init__(pos_start, pos_end, "Runtime Error", details)
        self.context = context

    def as_string(self):
        result = self.generate_traceback()
        result += f"{self.err_name}: {self.details}"
        result += f"\n{strings_with_arrows(self.pos_start.file_text, self.pos_start, self.pos_end)}"

        return result

    def generate_traceback(self):
        result = ""
        pos = self.pos_start
        context = self.context

        while context:
            result = f"File {pos.file_name}, line {str(pos.line + 1)}, in {context.display_name}\n" + result
            pos = context.parent_entry_pos
            context = context.parent

        return "Traceback (most recent call last):\n" + result

# keep track of line and column number (for executing code from files)
class Position:
    def __init__(self, index, line, col, file_name, file_text) -> None:
        self.index = index
        self.line = line
        self.col = col
        self.file_name = file_name
        self.file_text = file_text

    def advance(self, current_char=None):
        self.index += 1
        self.col += 1

        if current_char == "\n":
            self.line += 1
            self.col = 0

        return self
    
    def copy(self):
        return Position(self.index, self.line, self.col, self.file_name, self.file_text)


# Token
class Token:
    def __init__(self, type, value=None, pos_start=None, pos_end=None) -> None:
        self.type = type
        self.value = value

        if pos_start:
            self.pos_start = pos_start.copy()
            self.pos_end = pos_start.copy()
            self.pos_end.advance()

        if pos_end:
            self.pos_end = pos_end

    def __repr__(self) -> str:
        if self.value:
            return f"{self.type}:{self.value}"
        
        return f"{self.type}"
    
    def matches(self, type_, value):
        return self.type == type_ and self.value == value


# Lexer
class Lexer:
    def __init__(self, text, file_name) -> None:
        self.file_name = file_name
        self.text = text
        self.pos = Position(-1, 0, -1, file_name, text)
        self.current_char = None
        self.advance()
    
    # iterate through the text
    def advance(self):
        self.pos.advance(self.current_char)
        self.current_char = self.text[self.pos.index] if self.pos.index < len(self.text) else None

    def make_token(self):
        tokens = []

        while self.current_char != None:
            if self.current_char in " \t":
                self.advance()
            elif self.current_char in ";\n":
                tokens.append(Token(TT_NEWLINE, pos_start=self.pos))
                self.advance()
            elif self.current_char in DIGITS:
                tokens.append(self.make_number())
            elif self.current_char in LETTERS:
                tokens.append(self.make_identifier())
            elif self.current_char == '"':
                tokens.append(self.make_string())
            elif self.current_char == "+":
                tokens.append(Token(TT_PLUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == '-':
                tokens.append(self.make_minus_or_arrow())
            elif self.current_char == '*':
                tokens.append(Token(TT_MUL, pos_start=self.pos))
                self.advance()
            elif self.current_char == '/':
                tokens.append(Token(TT_DIV, pos_start=self.pos))
                self.advance()
            elif self.current_char == '(':
                tokens.append(Token(TT_LPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(TT_RPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == '[':
                tokens.append(Token(TT_LSQUARE, pos_start=self.pos))
                self.advance()
            elif self.current_char == ']':
                tokens.append(Token(TT_RSQUARE, pos_start=self.pos))
                self.advance()
            elif self.current_char == "^":
                tokens.append(Token(TT_POW, pos_start=self.pos))
                self.advance()
            elif self.current_char == "!":
                token, error = self.make_not_equals()
                if error:
                    return [], error
                tokens.append(token)
            elif self.current_char == "=":
                tokens.append(self.make_equals())
            elif self.current_char == "<":
                tokens.append(self.make_less_than())
            elif self.current_char == ">":
                tokens.append(self.make_greater_than())
            elif self.current_char == ",":
                tokens.append(Token(TT_COMMA, pos_start=self.pos))
                self.advance()
            else:
                pos_start = self.pos.copy()

                char = self.current_char
                self.advance()

                return [], IllegalCharacterError(pos_start, self.pos, "'" + char + "'")

        tokens.append(Token(TT_EOF, pos_start=self.pos))
        return tokens, None

    def make_number(self):
        num_str = ""
        dot_count = 0
        pos_start = self.pos.copy()

        while self.current_char != None and self.current_char in DIGITS + ".":
            if self.current_char == ".":
                if dot_count == 1:
                    break

                dot_count += 1
                num_str += "."
            else:
                num_str += self.current_char
            
            self.advance()

        if dot_count == 0:
            return Token(TT_INT, int(num_str), pos_start, self.pos)
        else:
            return Token(TT_FLOAT, float(num_str), pos_start, self.pos)
        
    def make_identifier(self):
        id_str = ""
        pos_start = self.pos.copy()

        while self.current_char != None and self.current_char in LETTERS_DIGITS + "_":
            id_str += self.current_char
            self.advance()

        token_type = TT_KEYWORD if id_str in KEYWORDS else TT_IDENTIFIER

        return Token(token_type, id_str, pos_start, self.pos)
    
    def make_minus_or_arrow(self):
        token_type = TT_MINUS
        pos_start = self.pos.copy()
        self.advance()
        
        if self.current_char == ">":
            self.advance()
            token_type = TT_ARROW

        return Token(token_type, pos_start=pos_start, pos_end=self.pos)
    
    def make_not_equals(self):
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == "=":
            self.advance()
            return Token(TT_NE, pos_start=pos_start, pos_end=self.pos), None
        
        self.advance()
        return None, ExpectedCharError(pos_start, self.pos, "'=' comes after '!'")
    
    def make_equals(self):
        token_type = TT_EQUAL
        pos_start = self.pos.copy()
        self.advance()
        
        if self.current_char == '=':
            self.advance()
            token_type = TT_EE
        
        return Token(token_type, pos_start=pos_start, pos_end=self.pos)
    
    def make_less_than(self):
        token_type = TT_LT
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            token_type = TT_LTE

        return Token(token_type, pos_start=pos_start, pos_end=self.pos)

    def make_greater_than(self):
        token_type = TT_GT
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            token_type = TT_GTE

        return Token(token_type, pos_start=pos_start, pos_end=self.pos)
    
    def make_string(self):
        string = ""
        pos_start = self.pos.copy()
        escape_char = False

        self.advance()

        escape_characters = {
            "n" : "\n",
            "t" : "\t"
        }

        while self.current_char != None and (self.current_char != '"' or escape_char):
            if escape_char:
                string += escape_characters.get(self.current_char, self.current_char)
            else:
                if self.current_char == "\\":
                    escape_char = True
                else:
                    string += self.current_char

            self.advance()
            escape_char = False
        
        self.advance()
        return Token(TT_STRING, string, pos_start, self.pos)
        

class IfNode:
    def __init__(self, cases, else_case):
        self.cases = cases
        self.else_case = else_case

        self.pos_start = self.cases[0][0].pos_start
        self.pos_end = (self.else_case or self.cases[len(self.cases) - 1][0]).pos_end


class ForNode:
	def __init__(self, var_name_token, start_value_node, end_value_node, step_value_node, body_node):
		self.var_name_token = var_name_token
		self.start_value_node = start_value_node
		self.end_value_node = end_value_node
		self.step_value_node = step_value_node
		self.body_node = body_node
		self.pos_start = self.var_name_token.pos_start
		self.pos_end = self.body_node.pos_end

class WhileNode:
	def __init__(self, condition_node, body_node):
		self.condition_node = condition_node
		self.body_node = body_node
		self.pos_start = self.condition_node.pos_start
		self.pos_end = self.body_node.pos_end


class FunctionNode:
    def __init__(self, var_name_token, arg_name_tokens, body_node) -> None:
        self.var_name_token = var_name_token
        self.arg_name_tokens = arg_name_tokens
        self.body_node = body_node

        if self.var_name_token:
            self.pos_start = self.var_name_token.pos_start
        elif len(self.arg_name_tokens) > 0:
            self.pos_start = self.arg_name_tokens[0].pos_start
        else:
            self.pos_start = self.body_node.pos_start
        
        self.pos_end = self.body_node.pos_end


class CallNode:
    def __init__(self, node_to_call, arg_nodes) -> None:
        self.node_to_call = node_to_call
        self.arg_nodes = arg_nodes
        self.pos_start = self.node_to_call.pos_start

        if len(self.arg_nodes) > 0:
            self.pos_end = self.arg_nodes[len(self.arg_nodes) - 1].pos_end
        else:
            self.pos_end = self.node_to_call.pos_end


class VarAccessNode:
    def __init__(self, var_name_token) -> None:
        self.var_name_token = var_name_token
        self.pos_start = self.var_name_token.pos_start
        self.pos_end = self.var_name_token.pos_end


class VarAssignNode:
    def __init__(self, var_name_token, value_node) -> None:
        self.var_name_token = var_name_token
        self.value_node = value_node
        self.pos_start = self.var_name_token.pos_start
        self.pos_end = self.value_node.pos_end


class NumberNode:
    def __init__(self, token) -> None:
        self.token = token
        self.pos_start = self.token.pos_start
        self.pos_end = self.token.pos_end

    def __repr__(self) -> str:
        return f"{self.token}"


class StringNode:
    def __init__(self, token) -> None:
        self.token = token
        self.pos_start = self.token.pos_start
        self.pos_end = self.token.pos_end

    def __repr__(self) -> str:
        return f"{self.token}"
    

class ListNode:
    def __init__(self, element_nodes, pos_start, pos_end) -> None:
        self.element_nodes = element_nodes
        self.pos_start = pos_start
        self.pos_end = pos_end


class BinaryOperationNode:
    def __init__(self, left_node, op_token, right_node) -> None:
        self.left_node = left_node
        self.op_token = op_token
        self.right_node = right_node
        self.pos_start = self.left_node.pos_start
        self.pos_end = self.right_node.pos_end

    def __repr__(self) -> str:
        return f"({self.left_node}, {self.op_token}, {self.right_node})"
    

class UnaryOperationNode:
    def __init__(self, op_token, node) -> None:
        self.op_token = op_token
        self.node = node
        self.pos_start = self.op_token.pos_start
        self.pos_end = self.node.pos_end

    def __repr__(self) -> str:
        return f"({self.op_token}, {self.node})"
    

class ParseResult:
    def __init__(self) -> None:
        self.error = None
        self.node = None
        self.advance_count = 0

    def register_advance(self):
        self.advance_count += 1

    def register(self, res):
        self.advance_count += res.advance_count
        # check if result is parse result
        if res.error:
            self.error = res.error
        return res.node
    
    def success(self, node):
        self.node = node
        return self
    
    def failure(self, error):
        if not self.error or self.advance_count == 0:
            self.error = error
        return self


class Parser:
    def __init__(self, tokens) -> None:
        self.tokens = tokens
        self.token_index = -1
        self.advance()

    def advance(self):
        self.token_index += 1

        if self.token_index < len(self.tokens):
            self.current_token = self.tokens[self.token_index]
        
        return self.current_token
    
    def parse(self):
        res = self.expression()
        if not res.error and self.current_token.type != TT_EOF:
            return res.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected '+', '-', '*' or '/'"))
        return res
    
    def power(self):
        return self.binary_op(self.call, (TT_POW, ), self.factor)
    
    def list_expression(self):
        res = ParseResult()
        element_nodes = []
        pos_start = self.current_token.pos_start.copy()

        if self.current_token.type != TT_LSQUARE:
            return res.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected '['"))
        
        res.register_advance()
        self.advance()

        if self.current_token.type == TT_RSQUARE:
            res.register_advance()
            self.advance()
        else:
            element_nodes.append(res.register(self.expression()))

            if res.error:
                return res.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected ']', int, float, identifier, 'var', 'if', 'for', 'while', 'function', '+', '-', '(', '[' or 'not'"))
            
            while self.current_token.type == TT_COMMA:
                res.register_advance()
                self.advance()

                element_nodes.append(res.register(self.expression()))
                if res.error:
                    return res
                
            if self.current_token.type != TT_RSQUARE:
                return res.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected ',' or ']'"))
            
            res.register_advance()
            self.advance()

        return res.success(ListNode(element_nodes, pos_start, self.current_token.pos_end.copy()))
    
    def if_expression(self):
        res = ParseResult()
        cases = []
        else_case = None

        if not self.current_token.matches(TT_KEYWORD, "if"):
            return res.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, f"Expected 'if'"))

        res.register_advance()
        self.advance()

        condition = res.register(self.expression())
        if res.error:
            return res

        if not self.current_token.matches(TT_KEYWORD, "then"):
            return res.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, f"Expected 'then'"))

        res.register_advance()
        self.advance()

        expression = res.register(self.expression())
        if res.error:
            return res
        cases.append((condition, expression))

        while self.current_token.matches(TT_KEYWORD, "elif"):
            res.register_advance()
            self.advance()

            condition = res.register(self.expression())
            if res.error:
                return res

            if not self.current_token.matches(TT_KEYWORD, "then"):
                return res.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, f"Expected 'then'"))

            res.register_advance()
            self.advance()

            expression = res.register(self.expression())
            if res.error:
                return res
            cases.append((condition, expression))

        if self.current_token.matches(TT_KEYWORD, "else"):
            res.register_advance()
            self.advance()

            else_case = res.register(self.expression())
            if res.error:
                return res

        return res.success(IfNode(cases, else_case))
    
    def for_expression(self):
        res = ParseResult()

        if not self.current_token.matches(TT_KEYWORD, "for"):
            return res.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected 'for'"))
        
        res.register_advance()
        self.advance()

        if self.current_token.type != TT_IDENTIFIER:
            return res.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected identifier"))
        
        var_name = self.current_token
        res.register_advance()
        self.advance()

        if self.current_token.type != TT_EQUAL:
            return res.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected '='"))
        
        res.register_advance()
        self.advance()

        start_value = res.register(self.expression())
        if res.error:
            return res
        
        if not self.current_token.matches(TT_KEYWORD, "to"):
            return res.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected 'to'"))
        
        res.register_advance()
        self.advance()

        end_value = res.register(self.expression())
        if res.error:
            return res
        
        # optional step keyword
        if self.current_token.matches(TT_KEYWORD, "step"):
            res.register_advance()
            self.advance()

            step_value = res.register(self.expression())
            if res.error:
                return res
        else:
            step_value = None

        if not self.current_token.matches(TT_KEYWORD, "then"):
            return res.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected 'then'"))
        
        res.register_advance()
        self.advance()

        body = res.register(self.expression())
        if res.error:
            return res
        
        return res.success(ForNode(var_name, start_value, end_value, step_value, body))

    def while_expression(self):
        res = ParseResult()

        if not self.current_token.matches(TT_KEYWORD, "while"):
            return res.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected 'while'"))
        
        res.register_advance()
        self.advance()

        condition = res.register(self.expression())
        if res.error:
            return res
        
        if not self.current_token.matches(TT_KEYWORD, "then"):
            return res.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected 'then'"))
        
        res.register_advance()
        self.advance()

        body = res.register(self.expression())
        if res.error:
            return res
        
        return res.success(WhileNode(condition, body))
    
    def function_definition(self):
        res = ParseResult()

        if not self.current_token.matches(TT_KEYWORD, "function"):
            return res.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected 'function'"))
        
        res.register_advance()
        self.advance()

        if self.current_token.type == TT_IDENTIFIER:
            var_name_token = self.current_token

            res.register_advance()
            self.advance()

            if self.current_token.type != TT_LPAREN:
                return res.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected identifier or '('"))
        else:
            var_name_token = None
            
            if self.current_token.type != TT_LPAREN:
                return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected identifier or '('"))
        
        res.register_advance()
        self.advance()
        arg_name_tokens = [] # for all the argument names

        if self.current_token.type == TT_IDENTIFIER:
            arg_name_tokens.append(self.current_token)

            res.register_advance()
            self.advance()

            while self.current_token.type == TT_COMMA:
                res.register_advance()
                self.advance()

                if self.current_token.type != TT_IDENTIFIER:
                    return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected identifier"))
                
                arg_name_tokens.append(self.current_token)
                res.register_advance()
                self.advance()

            if self.current_token.type != TT_RPAREN:
                return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected ',' or ')'"))
        else:
            if self.current_token.type != TT_RPAREN:
                return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected identifier or ')'"))
        
        res.register_advance()
        self.advance()

        if self.current_token.type != TT_ARROW:
            return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '->'"))
        
        res.register_advance()
        self.advance()

        node_to_return = res.register(self.expression())
        if res.error:
            return res
        
        return res.success(FunctionNode(var_name_token, arg_name_tokens, node_to_return))
    
    def call(self):
        res = ParseResult()
        atom = res.register(self.atom())
        if res.error:
            return res
        
        if self.current_token.type == TT_LPAREN:
            res.register_advance()
            self.advance()
            arg_nodes = []

            if self.current_token.type == TT_RPAREN:
                res.register_advance()
                self.advance()
            else:
                arg_nodes.append(res.register(self.expression()))

                if res.error:
                    return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected int, float, identifier, 'var', 'if', 'for', 'while', 'function', 'not', '+', '-', '(', '[' or ')' "))

                while self.current_token.type == TT_COMMA:
                    res.register_advance()
                    self.advance()

                    arg_nodes.append(res.register(self.expression()))
                    if res.error:
                        return res
                    
                if self.current_token.type != TT_RPAREN:
                    return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected ',' or ')'"))
                
                res.register_advance()
                self.advance()
            
            return res.success(CallNode(atom, arg_nodes))
        return res.success(atom) # if no parentheses (no calling)
    
    def atom(self):
        res = ParseResult()
        token = self.current_token

        if token.type in (TT_INT, TT_FLOAT):
            res.register_advance()
            self.advance()
            return res.success(NumberNode(token))
        elif token.type == TT_STRING:
            res.register_advance()
            self.advance()
            return res.success(StringNode(token))
        elif token.type == TT_IDENTIFIER:
            res.register_advance()
            self.advance()
            return res.success(VarAccessNode(token))
        elif token.type == TT_LPAREN:
            res.register_advance()
            self.advance()
            expr = res.register(self.expression())

            if res.error:
                return res
            
            if self.current_token.type == TT_RPAREN:
                res.register_advance()
                self.advance()
                return res.success(expr)
            else:
                return res.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected ')'"))
        elif token.type == TT_LSQUARE:
            list_expr = res.register(self.list_expression())
            if res.error:
                return res
            return res.success(list_expr)
        elif token.matches(TT_KEYWORD, "if"):
            if_expression = res.register(self.if_expression())
            if res.error:
                return res
            return res.success(if_expression)
        elif token.matches(TT_KEYWORD, "for"):
            for_expr = res.register(self.for_expression())
            if res.error:
                return res
            return res.success(for_expr)
        elif token.matches(TT_KEYWORD, "while"):
            while_expr = res.register(self.while_expression())
            if res.error:
                return res
            return res.success(while_expr)
        elif token.matches(TT_KEYWORD, "function"):
            function_def = res.register(self.function_definition())
            if res.error:
                return res
            return res.success(function_def)
            
        return res.failure(InvalidSyntaxError(token.pos_start, token.pos_end, "Expected int, float, identifier, '+', '-' or '(', '[' 'if', 'for', 'while', 'function'"))
    
    def factor(self):
        res = ParseResult()
        token = self.current_token

        if token.type in (TT_PLUS, TT_MINUS):
            res.register_advance()
            self.advance()
            factor = res.register(self.factor())

            if res.error:
                return res
            return res.success(UnaryOperationNode(token, factor))
        
        return self.power()

    def term(self):
        return self.binary_op(self.factor, (TT_MUL, TT_DIV))
    
    def arithmetic_expression(self):
        return self.binary_op(self.term, (TT_PLUS, TT_MINUS))
    
    def comparison_expression(self):
        res = ParseResult()
        
        if self.current_token.matches(TT_KEYWORD, "not"):
            op_token = self.current_token
            res.register_advance()
            self.advance()

            node = res.register(self.comparison_expression())
            if res.error: 
                return res
            return res.success(UnaryOperationNode(op_token, node))
		
        node = res.register(self.binary_op(self.arithmetic_expression, (TT_EE, TT_NE, TT_LT, TT_GT, TT_LTE, TT_GTE)))
		
        if res.error:
            return res.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected int, float, identifier, '+', '-', '(', '[' or 'Not'"))

        return res.success(node)

    def expression(self):
        res = ParseResult()

        # check for keyword var
        if self.current_token.matches(TT_KEYWORD, "var"):
            res.register_advance()
            self.advance()

            # check for identifier 
            if self.current_token.type != TT_IDENTIFIER:
                return res.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected identifier"))
            
            var_name = self.current_token
            res.register_advance()
            self.advance()

            if self.current_token.type != TT_EQUAL:
                return res.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected '='"))
            res.register_advance()
            self.advance()

            expression = res.register(self.expression())
            if res.error:
                return res
            
            return res.success(VarAssignNode(var_name, expression))

        node = res.register(self.binary_op(self.comparison_expression, ((TT_KEYWORD, "and"), (TT_KEYWORD, "or"))))

        if res.error:
            return res.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected int, float, identifier, 'var', 'if', 'for', 'while', 'function', '+', '-', '(' or '['"))

        return res.success(node)

    def binary_op(self, function_a, ops, function_b=None):
        if function_b == None:
            function_b = function_a

        res = ParseResult()
        left = res.register(function_a())
        if res.error:
            return res

        # quick fix for specifying types, not very fast, will have to come back to this
        while self.current_token.type in ops or (self.current_token.type, self.current_token.value) in ops:
            op_token = self.current_token
            res.register_advance()
            self.advance()
            right = res.register(function_b())
            if res.error:
                return res
            left = BinaryOperationNode(left, op_token, right)
        
        return res.success(left)
    

class RuntimeResult:
    def __init__(self) -> None:
        self.value = None
        self.error = None

    def register(self, res):
        if res.error:
            self.error = res.error

        return res.value
    
    def success(self, value):
        self.value = value
        return self

    def failure(self, error):
        self.error = error
        return self
    

class Context:
    def __init__(self, display_name, parent=None, parent_entry_pos=None) -> None:
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos = parent_entry_pos
        self.symbol_table = None


class SymbolTable:
    def __init__(self, parent=None) -> None:
        self.symbols = {}
        self.parent = parent

    def get(self, name):
        value = self.symbols.get(name, None)

        if value == None and self.parent:
            return self.parent.get(name)
        
        return value

    def set(self, name, value):
        self.symbols[name] = value
    
    def remove(self, name):
        del self.symbols[name]


class Value:
    def __init__(self):
        self.set_pos()
        self.set_context()

    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self

    def set_context(self, context=None):
        self.context = context
        return self

    def add(self, other):
        return None, self.illegal_operation(other)

    def sub(self, other):
        return None, self.illegal_operation(other)

    def mul(self, other):
        return None, self.illegal_operation(other)

    def div(self, other):
        return None, self.illegal_operation(other)

    def pow(self, other):
        return None, self.illegal_operation(other)

    def compare_eq(self, other):
        return None, self.illegal_operation(other)

    def compare_ne(self, other):
        return None, self.illegal_operation(other)

    def compare_lt(self, other):
        return None, self.illegal_operation(other)

    def compare_gt(self, other):
        return None, self.illegal_operation(other)

    def compare_lte(self, other):
        return None, self.illegal_operation(other)

    def compare_gte(self, other):
        return None, self.illegal_operation(other)

    def ander(self, other):
        return None, self.illegal_operation(other)

    def orer(self, other):
        return None, self.illegal_operation(other)

    def notter(self):
        return None, self.illegal_operation()

    def execute(self, args):
        return RuntimeResult().failure(self.illegal_operation())

    def copy(self):
        raise Exception('No copy method defined')

    def is_true(self):
        return False

    def illegal_operation(self, other=None):
        if not other:
            other = self
        return RuntimeResult(self.pos_start, other.pos_end, 'Illegal operation', self.context)
    

# for storing numbers
class Number(Value):
    def __init__(self, value) -> None:
        super().__init__()
        self.value = value

    # def set_pos(self, pos_start=None, pos_end=None):
    #     self.pos_start = pos_start
    #     self.pos_end = pos_end
    #     return self
    
    # def set_context(self, context=None):
    #     self.context = context
    #     return self
    
    def add(self, other):
        if isinstance(other, Number):
            return Number(self.value + other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)
        
    def sub(self, other):
        if isinstance(other, Number):
            return Number(self.value - other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)
        
    def mul(self, other):
        if isinstance(other, Number):
            return Number(self.value * other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)
    
    def div(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RuntimeError(other.pos_start, other.pos_end, "Division by 0", self.context)
            return Number(self.value / other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)
        
    def pow(self, other):
        if isinstance(other, Number):
            return Number(self.value ** other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)
        
    def compare_ee(self, other):
        if isinstance(other, Number):
            return Number(int(self.value == other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def compare_ne(self, other):
        if isinstance(other, Number):
            return Number(int(self.value != other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def compare_lt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value < other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def compare_gt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value > other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def compare_lte(self, other):
        if isinstance(other, Number):
            return Number(int(self.value <= other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def compare_gte(self, other):
        if isinstance(other, Number):
            return Number(int(self.value >= other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def ander(self, other):
        if isinstance(other, Number):
            return Number(int(self.value and other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def orer(self, other):
        if isinstance(other, Number):
            return Number(int(self.value or other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def notter(self):
        return Number(1 if self.value == 0 else 0).set_context(self.context), None
        
    def copy(self):
        copy = Number(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        
        return copy
    
    def is_true(self):
        return self.value != 0
        
    def __repr__(self) -> str:
        return str(self.value)
    

Number.null = Number(0)
Number.true = Number(1)
Number.false = Number(0)
Number.math_PI = Number(math.pi)


class String(Value):
    def __init__(self, value):
        super().__init__()
        self.value = value
    
    def add(self, other):
        if isinstance(other, String):
            return String(self.value + other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def mul(self, other):
        if isinstance(other, Number):
            return String(self.value * other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def is_true(self):
        return len(self.value) > 0

    def copy(self):
        copy = String(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)

        return copy
    
    def __str__(self) -> str:
        return self.value

    def __repr__(self):
        return f'"{self.value}"'
    

class BaseFunction(Value):
    def __init__(self, name):
        super().__init__()
        self.name = name or "<anon>"

    def generate_new_context(self):
        new_context = Context(self.name, self.context, self.pos_start)
        new_context.symbol_table = SymbolTable(new_context.parent.symbol_table)

        return new_context
    
    def check_args(self, arg_names, args):
        res = RuntimeResult()

        if len(args) > len(arg_names):
            return res.failure(RuntimeError(self.pos_start, self.pos_end, f"{len(args)} - {len(arg_names)} too many args passed into {self}", self.context))
        
        if len(args) < len(arg_names):
            return res.failure(RuntimeError(self.pos_start, self.pos_end, f"{len(arg_names) - len(args)} too few args passed into {self}", self.context))
        
        return res.success(None)
    
    def populate_args(self, arg_names, args, exec_context):
        for i in range(len(args)):
            arg_name = arg_names[i]
            arg_value = args[i]
            arg_value.set_context(exec_context)
            exec_context.symbol_table.set(arg_name, arg_value)

    def check_and_populate_args(self, arg_names, args, exec_context):
        res = RuntimeResult()

        res.register(self.check_args(arg_names, args))
        if res.error:
            return res
        
        self.populate_args(arg_names, args, exec_context)

        return res.success(None)
    

class Function(BaseFunction):
    def __init__(self, name, body_node, arg_names):
        super().__init__(name)
        self.body_node = body_node
        self.arg_names = arg_names

    def execute(self, args):
        res = RuntimeResult()
        interpreter = Interpreter()
        exec_context = self.generate_new_context()

        res.register(self.check_and_populate_args(self.arg_names, args, exec_context))
        if res.error:
            return res

        value = res.register(interpreter.visit(self.body_node, exec_context))
        if res.error:
            return res
        
        return res.success(value)

    def copy(self):
        copy = Function(self.name, self.body_node, self.arg_names)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)

        return copy

    def __repr__(self):
        return f"<function {self.name}>"
    

class BuiltinFunction(BaseFunction):
    def __init__(self, name):
        super().__init__(name)
        
    def execute(self, args):
        res = RuntimeResult()
        exec_context = self.generate_new_context()

        method_name = f'execute_{self.name}'
        method = getattr(self, method_name, self.no_visit_method)

        res.register(self.check_and_populate_args(method.arg_names, args, exec_context))
        if res.error:
            return res

        return_value = res.register(method(exec_context))
        if res.error:
            return res
        
        return res.success(return_value)
    
    def no_visit_method(self, node, context):
        raise Exception(f'No execute_{self.name} method defined')
    
    def copy(self):
        copy = BuiltinFunction(self.name)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)

        return copy

    def __repr__(self):
        return f"<built-in function {self.name}>"
    

    # Built-in functions code
    def execute_print(self, exec_context):
        print(str(exec_context.symbol_table.get('value')))
        return RuntimeResult().success(Number.null)
    execute_print.arg_names = ['value']

    def execute_print_ret(self, exec_context):
        return RuntimeResult().success(String(str(exec_context.symbol_table.get('value'))))
    execute_print_ret.arg_names = ['value']
    
    def execute_input(self, exec_context):
        text = input()
        return RuntimeResult().success(String(text))
    execute_input.arg_names = []

    def execute_input_int(self, exec_context):
        while True:
            text = input()
            try:
                number = int(text)
                break
            except ValueError:
                print(f"'{text}' must be an integer.")
        return RuntimeResult().success(Number(number))
    execute_input_int.arg_names = []

    def execute_clear(self, exec_context):
        os.system('cls' if os.name == 'nt' else 'clear')  # cls for window, clear for unix
        return RuntimeResult().success(Number.null)
    execute_clear.arg_names = []

    def execute_is_number(self, exec_context):
        is_number = isinstance(exec_context.symbol_table.get("value"), Number)
        return RuntimeResult().success(Number.true if is_number else Number.false)
    execute_is_number.arg_names = ["value"]

    def execute_is_string(self, exec_context):
        is_string = isinstance(exec_context.symbol_table.get("value"), String)
        return RuntimeResult().success(Number.true if is_string else Number.false)
    execute_is_string.arg_names = ["value"]

    def execute_is_list(self, exec_context):
        is_list = isinstance(exec_context.symbol_table.get("value"), List)
        return RuntimeResult().success(Number.true if is_list else Number.false)
    execute_is_list.arg_names = ["value"]

    def execute_is_function(self, exec_context):
        is_function = isinstance(exec_context.symbol_table.get("value"), BaseFunction)
        return RuntimeResult().success(Number.true if is_function else Number.false)
    execute_is_function.arg_names = ["value"]

    def execute_append(self, exec_context):
        list_ = exec_context.symbol_table.get("list")
        value = exec_context.symbol_table.get("value")

        if not isinstance(list_, List):
            return RuntimeResult().failure(RuntimeError(self.pos_start, self.pos_end, "1st argument must be a list", exec_context))

        list_.elements.append(value)
        return RuntimeResult().success(Number.null)
    execute_append.arg_names = ["list", "value"]

    def execute_pop(self, exec_context):
        list_ = exec_context.symbol_table.get("list")
        index = exec_context.symbol_table.get("index")

        if not isinstance(list_, List):
            return RuntimeResult().failure(RuntimeError(self.pos_start, self.pos_end, "1st argument must be a list", exec_context))
        
        if not isinstance(index, Number):
            return RuntimeResult().failure(RuntimeError(self.pos_start, self.pos_end, "2nd argument must be a number", exec_context))
        
        try:
            element = list_.elements.pop(index.value)
        except:
            return RuntimeResult().failure(RuntimeError(self.pos_start, self.pos_end, 'Element at this index could not be removed from list because index is out of bounds', exec_context))
        
        return RuntimeResult().success(element)
    execute_pop.arg_names = ["list", "index"]

    def execute_extend(self, exec_context):
        listA = exec_context.symbol_table.get("listA")
        listB = exec_context.symbol_table.get("listB")

        if not isinstance(listA, List):
            return RuntimeResult().failure(RuntimeError(self.pos_start, self.pos_end, "1st argument must be a list", exec_context))

        if not isinstance(listB, List):
            return RuntimeResult().failure(RuntimeError(self.pos_start, self.pos_end, "2nd argument must be a list", exec_context))

        listA.elements.extend(listB.elements)
        return RuntimeResult().success(Number.null)
    execute_extend.arg_names = ["listA", "listB"]

BuiltinFunction.print = BuiltinFunction("print")
BuiltinFunction.print_ret = BuiltinFunction("print_ret")
BuiltinFunction.input = BuiltinFunction("input")
BuiltinFunction.input_int = BuiltinFunction("input_int")
BuiltinFunction.clear = BuiltinFunction("clear")
BuiltinFunction.is_number = BuiltinFunction("is_number")
BuiltinFunction.is_string = BuiltinFunction("is_string")
BuiltinFunction.is_list = BuiltinFunction("is_list")
BuiltinFunction.is_function  = BuiltinFunction("is_function")
BuiltinFunction.append = BuiltinFunction("append")
BuiltinFunction.pop = BuiltinFunction("pop")
BuiltinFunction.extend = BuiltinFunction("extend")

class List(Value):
    def __init__(self, elements):
        super().__init__()
        self.elements = elements

    # append elements to list
    def add(self, other):
        new_list = self.copy()
        new_list.elements.append(other)

        return new_list, None

    # remove element from list
    def sub(self, other):
        if isinstance(other, Number):
            new_list = self.copy()
            try:
                new_list.elements.pop(other.value)

                return new_list, None
            except:
                return None, RuntimeError(other.pos_start, other.pos_end, 'Element at this index could not be removed from list as index is out of bounds', self.context)
        else:
            return None, Value.illegal_operation(self, other)

    # concatenate to list to list
    def mul(self, other):
        if isinstance(other, List):
            new_list = self.copy()
            new_list.elements.extend(other.elements)

            return new_list, None
        else:
            return None, Value.illegal_operation(self, other)

    # get element from list
    def div(self, other):
        if isinstance(other, Number):
            try:
                return self.elements[other.value], None
            except:
                return None, RuntimeError(other.pos_start, other.pos_end, 'Element at this index could not be retrieved from list as index is out of bounds', self.context)
        else:
            return None, Value.illegal_operation(self, other)
  
    def copy(self):
        copy = List(self.elements)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        
        return copy
    
    def __str__(self) -> str:
        return ", ".join([str(x) for x in self.elements])

    def __repr__(self):
        return f'[{", ".join([str(x) for x in self.elements])}]'
    

class Interpreter:
    def visit(self, node, context):
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, self.no_visit_method)
        return method(node, context)
    
    def no_visit_method(self, node, context):
        raise Exception(f"No visit_{type(node).__name__} method defined")
    
    def visit_NumberNode(self, node, context):
        return RuntimeResult().success(Number(node.token.value).set_context(context).set_pos(node.pos_start, node.pos_end))
    
    def visit_StringNode(self, node, context):
        return RuntimeResult().success(String(node.token.value).set_context(context).set_pos(node.pos_start, node.pos_end))
    
    def visit_ListNode(self, node, context):
        res = RuntimeResult()
        elements = []

        for element_node in node.element_nodes:
            elements.append(res.register(self.visit(element_node, context)))

            if res.error:
                return res
            
        return res.success(List(elements).set_context(context).set_pos(node.pos_start, node.pos_end))
    
    def visit_VarAccessNode(self, node, context):
        res = RuntimeResult()
        var_name = node.var_name_token.value
        value = context.symbol_table.get(var_name)

        if not value:
            return res.failure(RuntimeError(node.pos_start, node.pos_end, f"'{var_name}' is not defined", context))
        
        value = value.copy().set_context(context).set_pos(node.pos_start, node.pos_end)
        return res.success(value)
    
    def visit_VarAssignNode(self, node, context):
        res = RuntimeResult()
        var_name = node.var_name_token.value
        value = res.register(self.visit(node.value_node, context))

        if res.error:
            return res
        
        context.symbol_table.set(var_name, value)
        return res.success(value)

    def visit_BinaryOperationNode(self, node, context):
        res = RuntimeResult()
        left = res.register(self.visit(node.left_node, context))
        if res.error: return res
        right = res.register(self.visit(node.right_node, context))
        if res.error: return res

        if node.op_token.type == TT_PLUS:
            result, error = left.add(right)
        elif node.op_token.type == TT_MINUS:
            result, error = left.sub(right)
        elif node.op_token.type == TT_MUL:
            result, error = left.mul(right)
        elif node.op_token.type == TT_DIV:
            result, error = left.div(right)
        elif node.op_token.type == TT_POW:
            result, error = left.pow(right)
        elif node.op_token.type == TT_EE:
            result, error = left.compare_ee(right)
        elif node.op_token.type == TT_NE:
            result, error = left.compare_ne(right)
        elif node.op_token.type == TT_LT:
            result, error = left.compare_lt(right)
        elif node.op_token.type == TT_GT:
            result, error = left.compare_gt(right)
        elif node.op_token.type == TT_LTE:
            result, error = left.compare_lte(right)
        elif node.op_token.type == TT_GTE:
            result, error = left.compare_gte(right)
        elif node.op_token.matches(TT_KEYWORD, "and"):
            result, error = left.ander(right)
        elif node.op_token.matches(TT_KEYWORD, "or"):
            result, error = left.orer(right)


        if error:
            return res.failure(error)

        return res.success(result.set_pos(node.pos_start, node.pos_end))
    
    def visit_UnaryOperationNode(self, node, context):
        res = RuntimeResult()
        number = res.register(self.visit(node.node, context))
        if res.error:
            return res

        if node.op_token.type == TT_MINUS:
            number, error = number.mul(Number(-1))
        elif node.op_token.matches(TT_KEYWORD, "not"):
            number, error = number.notter()

        if error:
            return res.failure(error)
            
        return res.success(number.set_pos(node.pos_start, node.pos_end))
    
    def visit_IfNode(self, node, context):
        res = RuntimeResult()

        for condition, expression in node.cases:
            condition_value = res.register(self.visit(condition, context))
            if res.error:
                return res

            if condition_value.is_true():
                expression_value = res.register(self.visit(expression, context))
                if res.error:
                    return res
                return res.success(expression_value)

        if node.else_case:
            else_value = res.register(self.visit(node.else_case, context))
            if res.error:
                return res
            return res.success(else_value)

        return res.success(None)
    
    def visit_ForNode(self, node, context):
        res = RuntimeResult()
        elements = []

        start_value = res.register(self.visit(node.start_value_node, context))
        if res.error:
            return res

        end_value = res.register(self.visit(node.end_value_node, context))
        if res.error:
            return res

        if node.step_value_node:
            step_value = res.register(self.visit(node.step_value_node, context))
            if res.error:
                return res
        else:
            step_value = Number(1)

        i = start_value.value

        if step_value.value >= 0:
            condition = lambda: i < end_value.value
        else:
            condition = lambda: i > end_value.value
		
        while condition():
            context.symbol_table.set(node.var_name_token.value, Number(i)) # for accessing i within the loop
            i += step_value.value

            elements.append(res.register(self.visit(node.body_node, context)))
            if res.error:
                return res

        return res.success(List(elements).set_context(context).set_pos(node.pos_start, node.pos_end))
    
    def visit_WhileNode(self, node, context):
        res = RuntimeResult()
        elements = []

        while True:
            condition = res.register(self.visit(node.condition_node, context))
            if res.error:
                return res

            if not condition.is_true():
                break

            elements.append(res.register(self.visit(node.body_node, context)))
            if res.error:
                return res

        return res.success(List(elements).set_context(context).set_pos(node.pos_start, node.pos_end))
    
    def visit_FunctionNode(self, node, context):
        res = RuntimeResult()

        function_name = node.var_name_token.value if node.var_name_token else None
        body_node = node.body_node
        arg_names = [arg_name.value for arg_name in node.arg_name_tokens]
        function_value = Function(function_name, body_node, arg_names).set_context(context).set_pos(node.pos_start, node.pos_end)

        if node.var_name_token:
            context.symbol_table.set(function_name, function_value)
        
        return res.success(function_value)
    
    def visit_CallNode(self, node, context):
        res = RuntimeResult()
        args = []

        value_to_call = res.register(self.visit(node.node_to_call, context))
        if res.error:
            return res
        value_to_call = value_to_call.copy().set_pos(node.pos_start, node.pos_end)

        for arg_node in node.arg_nodes:
            args.append(res.register(self.visit(arg_node, context)))
            if res.error:
                return res
            
        return_value = res.register(value_to_call.execute(args))
        if res.error:
            return res
        
        return_value = return_value.copy().set_context(context).set_pos(node.pos_start, node.pos_end)
        
        return res.success(return_value)


global_symbol_table = SymbolTable()
global_symbol_table.set("NULL", Number.null)
global_symbol_table.set("true", Number.false)
global_symbol_table.set("false", Number.true)
global_symbol_table.set("math_pi", Number.math_PI)
global_symbol_table.set("print", BuiltinFunction.print)
global_symbol_table.set("print_ret", BuiltinFunction.print_ret)
global_symbol_table.set("input", BuiltinFunction.input)
global_symbol_table.set("input_int", BuiltinFunction.input_int)
global_symbol_table.set("clear", BuiltinFunction.clear)
global_symbol_table.set("cls", BuiltinFunction.clear)
global_symbol_table.set("is_num", BuiltinFunction.is_number)
global_symbol_table.set("is_str", BuiltinFunction.is_string)
global_symbol_table.set("is_list", BuiltinFunction.is_list)
global_symbol_table.set("is_funcion", BuiltinFunction.is_function)
global_symbol_table.set("append", BuiltinFunction.append)
global_symbol_table.set("pop", BuiltinFunction.pop)
global_symbol_table.set("extend", BuiltinFunction.extend)

def run(text, file_name):
    # generate tokens
    lexer = Lexer(text, file_name)
    tokens, error = lexer.make_token()

    if error:
        return None, error

    # generate AST
    parser = Parser(tokens)
    ast = parser.parse()

    if ast.error:
        return None, ast.error
    
    interpreter = Interpreter()
    root_context = Context("<module>")
    root_context.symbol_table = global_symbol_table
    result = interpreter.visit(ast.node, root_context)

    return result.value, result.error
