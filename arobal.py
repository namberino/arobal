from string_format import *
import string

DIGITS = "0123456789"
LETTERS = string.ascii_letters
LETTERS_DIGITS = LETTERS + DIGITS

KEYWORDS = [
    "VAR"
]

# Token types
TT_INT = "INT"
TT_FLOAT = "FLOAT"
TT_PLUS = "PLUS"
TT_MINUS = "MINUS"
TT_MUL = "MUL"
TT_DIV = "DIV"
TT_POW = "POW"
TT_LPAREN = "LPAREN"
TT_RPAREN = "RPAREN"
TT_EQUAL = "EQ"
TT_IDENTIFIER = "IDENTIFIER"
TT_KEYWORD = "KEYWORD"
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
            elif self.current_char in DIGITS:
                tokens.append(self.make_number())
            elif self.current_char in LETTERS:
                tokens.append(self.make_identifier())
            elif self.current_char == "+":
                tokens.append(Token(TT_PLUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == '-':
                tokens.append(Token(TT_MINUS, pos_start=self.pos))
                self.advance()
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
            elif self.current_char == "^":
                tokens.append(Token(TT_POW, pos_start=self.pos))
                self.advance()
            elif self.current_char == "=":
                tokens.append(Token(TT_EQUAL, pos_start=self.pos))
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
            return res.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected +, -, * or /"))
        return res
    
    def power(self):
        return self.binary_op(self.atom, (TT_POW, ), self.factor)
    
    def atom(self):
        res = ParseResult()
        token = self.current_token

        if token.type in (TT_INT, TT_FLOAT):
            res.register_advance()
            self.advance()
            return res.success(NumberNode(token))
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
            
        return res.failure(InvalidSyntaxError(token.pos_start, token.pos_end, "Expected int, float, identifier, '+', '-' or '('"))
    
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

    def expression(self):
        res = ParseResult()

        # check for keyword VAR
        if self.current_token.matches(TT_KEYWORD, "VAR"):
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

        node = res.register(self.binary_op(self.term, (TT_PLUS, TT_MINUS)))

        if res.error:
            return res.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected 'VAR', int, float, identifier, '+', '-' or '('"))

        return res.success(node)

    def binary_op(self, function_a, ops, function_b=None):
        if function_b == None:
            function_b = function_a

        res = ParseResult()
        left = res.register(function_a())
        if res.error:
            return res

        while self.current_token.type in ops:
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
    def __init__(self) -> None:
        self.symbols = {}
        self.parent = None

    def get(self, name):
        value = self.symbols.get(name, None)

        if value == None and self.parent:
            return self.parent.get(name)
        
        return value

    def set(self, name, value):
        self.symbols[name] = value
    
    def remove(self, name):
        del self.symbols[name]
    

# for storing numbers
class Number:
    def __init__(self, value) -> None:
        self.value = value
        self.set_pos()
        self.set_context

    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self
    
    def set_context(self, context=None):
        self.context = context
        return self
    
    def add(self, other):
        if isinstance(other, Number):
            return Number(self.value + other.value).set_context(self.context), None
        
    def sub(self, other):
        if isinstance(other, Number):
            return Number(self.value - other.value).set_context(self.context), None
        
    def mul(self, other):
        if isinstance(other, Number):
            return Number(self.value * other.value).set_context(self.context), None
    
    def div(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RuntimeError(other.pos_start, other.pos_end, "Division by 0", self.context)
            return Number(self.value / other.value).set_context(self.context), None
        
    def pow(self, other):
        if isinstance(other, Number):
            return Number(self.value ** other.value).set_context(self.context), None
        
    def __repr__(self) -> str:
        return str(self.value)
    

class Interpreter:
    def visit(self, node, context):
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, self.no_visit_method)
        return method(node, context)
    
    def no_visit_method(self, node, context):
        raise Exception(f"No visit_{type(node).__name__} method defined")
    
    def visit_NumberNode(self, node, context):
        return RuntimeResult().success(Number(node.token.value).set_context(context).set_pos(node.pos_start, node.pos_end))
    
    def visit_VarAccessNode(self, node, context):
        res = RuntimeResult()
        var_name = node.var_name_token.value
        value = context.symbol_table.get(var_name)

        if not value:
            return res.failure(RuntimeError(node.pos_start, node.pos_end, f"'{var_name}' is not defined", context))
        
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

        if error:
            return res.failure(error)

        return res.success(number.set_pos(node.pos_start, node.pos_end))


global_symbol_table = SymbolTable()
global_symbol_table.set("NULL", Number(0))

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
