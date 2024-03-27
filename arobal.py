from string_format import *

DIGITS = "0123456789"

# Token types
TT_INT = "INT"
TT_FLOAT = "FLOAT"
TT_PLUS = "PLUS"
TT_MINUS = "MINUS"
TT_MUL = "MUL"
TT_DIV = "DIV"
TT_LPAREN = "LPAREN"
TT_RPAREN = "RPAREN"
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

    def register(self, res):
        # check if result is parse result
        if isinstance(res, ParseResult):
            if res.error:
                self.error = res.error
            return res.node
        
        return res
    
    def success(self, node):
        self.node = node
        return self
    
    def failure(self, error):
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
    
    def factor(self):
        res = ParseResult()
        token = self.current_token

        if token.type in (TT_PLUS, TT_MINUS):
            res.register(self.advance())
            factor = res.register(self.factor())

            if res.error:
                return res
            return res.success(UnaryOperationNode(token, factor))
        elif token.type in (TT_INT, TT_FLOAT):
            res.register(self.advance())
            return res.success(NumberNode(token))
        elif token.type == TT_LPAREN:
            res.register(self.advance())
            expr = res.register(self.expression())

            if res.error:
                return res
            
            if self.current_token.type == TT_RPAREN:
                res.register(self.advance())
                return res.success(expr)
            else:
                return res.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected ')'"))
        
        return res.failure(InvalidSyntaxError(token.pos_start, token.pos_end, "Expected an int or a float"))

    def term(self):
        return self.binary_op(self.factor, (TT_MUL, TT_DIV))

    def expression(self):
        return self.binary_op(self.term, (TT_PLUS, TT_MINUS))

    def binary_op(self, function, ops):
        res = ParseResult()
        left = res.register(function())
        if res.error:
            return res

        while self.current_token.type in ops:
            op_token = self.current_token
            res.register(self.advance())
            right = res.register(function())
            if res.error:
                return res
            left = BinaryOperationNode(left, op_token, right)
        
        return res.success(left)
    

# for storing numbers
class Number:
    def __init__(self, value) -> None:
        self.value = value
        self.set_pos()

    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self
    
    def add(self, other):
        if isinstance(other, Number):
            return Number(self.value + other.value)
        
    def sub(self, other):
        if isinstance(other, Number):
            return Number(self.value - other.value)
        
    def mul(self, other):
        if isinstance(other, Number):
            return Number(self.value * other.value)
    
    def div(self, other):
        if isinstance(other, Number):
            return Number(self.value / other.value)
        
    def __repr__(self) -> str:
        return str(self.value)
    

class Interpreter:
    def visit(self, node):
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, self.no_visit_method)
        return method(node)
    
    def no_visit_method(self, node):
        raise Exception(f"No visit_{type(node).__name__} method defined")
    
    def visit_NumberNode(self, node):
        return Number(node.token.value).set_pos(node.pos_start, node.pos_end)

    def visit_BinaryOperationNode(self, node):
        left = self.visit(node.left_node)
        right = self.visit(node.right_node)

        if node.op_token.type == TT_PLUS:
            result = left.add(right)
        elif node.op_token.type == TT_MINUS:
            result = left.sub(right)
        elif node.op_token.type == TT_MUL:
            result = left.mul(right)
        elif node.op_token.type == TT_DIV:
            result = left.div(right)

        return result.set_pos(node.pos_start, node.pos_end)
    
    def visit_UnaryOperationNode(self, node):
        number = self.visit(node.node)

        if node.op_token.type == TT_MINUS:
            number = number.mul(Number(-1))

        return number.set_pos(node.pos_start, node.pos_end)


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
    result = interpreter.visit(ast.node)

    return result, None
