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

class Error:
    def __init__(self, pos_start, pos_end, err_name, details) -> None:
        self.err_name = err_name
        self.details = details
        self.pos_start = pos_start
        self.pos_end = pos_end

    def as_string(self):
        result = f"{self.err_name}: {self.details}"
        result += f"\nFile {self.pos_start.file_name}, line {self.pos_start.line + 1}"

        return result

class IllegalCharacterError(Error):
    def __init__(self, pos_start, pos_end, details) -> None:
        super().__init__(pos_start, pos_end, "Illegal Character", details)


# keep track of line and column number (for executing code from files)
class Position:
    def __init__(self, index, line, col, file_name, file_text) -> None:
        self.index = index
        self.line = line
        self.col = col
        self.file_name = file_name
        self.file_text = file_text

    def advance(self, current_char):
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
    def __init__(self, type, value=None) -> None:
        self.type = type
        self.value = value

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
                tokens.append(Token(TT_PLUS))
                self.advance()
            elif self.current_char == '-':
                tokens.append(Token(TT_MINUS))
                self.advance()
            elif self.current_char == '*':
                tokens.append(Token(TT_MUL))
                self.advance()
            elif self.current_char == '/':
                tokens.append(Token(TT_DIV))
                self.advance()
            elif self.current_char == '(':
                tokens.append(Token(TT_LPAREN))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(TT_RPAREN))
                self.advance()
            else:
                pos_start = self.pos.copy()

                char = self.current_char
                self.advance()

                return [], IllegalCharacterError(pos_start, self.pos, "'" + char + "'")

        return tokens, None

    def make_number(self):
        num_str = ""
        dot_count = 0

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
            return Token(TT_INT, int(num_str))
        else:
            return Token(TT_FLOAT, float(num_str))
        

class NumberNode:
    def __init__(self, token) -> None:
        self.token = token

    def __repr__(self) -> str:
        return f"{self.token}"
    

class BinaryOperationNode:
    def __init__(self, left_node, op_token, right_node) -> None:
        self.left_node = left_node
        self.op_token = op_token
        self.right_node = right_node

    def __repr__(self) -> str:
        return f"({self.left_node}, {self.op_token}, {self.right_node})"
    

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
        return res
    
    def factor(self):
        token = self.current_token

        if token.type in (TT_INT, TT_FLOAT):
            self.advance()
            return NumberNode(token)

    def term(self):
        return self.binary_op(self.factor, (TT_MUL, TT_DIV))

    def expression(self):
        return self.binary_op(self.term, (TT_PLUS, TT_MINUS))

    def binary_op(self, function, ops):
        left = function()

        while self.current_token.type in ops:
            op_token = self.current_token
            self.advance()
            right = function()
            left = BinaryOperationNode(left, op_token, right)
        
        return left


def run(text, file_name):
    # generate tokens
    lexer = Lexer(text, file_name)
    tokens, error = lexer.make_token()

    if error:
        return None, error

    # generate AST
    parser = Parser(tokens)
    ast = parser.parse()

    return ast, None
