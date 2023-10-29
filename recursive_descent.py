import abc
import sys
import enum
import dataclasses


class ParseError(Exception):
    pass


class TokenType(enum.Enum):
    NUMBER = enum.auto()
    PLUS = enum.auto()
    MINUS = enum.auto()
    STAR = enum.auto()
    SLASH = enum.auto()
    LEFT_PAREN = enum.auto()
    RIGHT_PAREN = enum.auto()
    EOF = enum.auto()


@dataclasses.dataclass()
class Token:
    type: TokenType
    lexeme: str | None
    literal: str | float | None
    start_at: int
    end_at: int


class Visitor(abc.ABC):

    @abc.abstractmethod
    def visit_binary_expression(self, expr):
        raise NotImplementedError()

    @abc.abstractmethod
    def visit_grouping_expression(self, expr):
        raise NotImplementedError()

    @abc.abstractmethod
    def visit_literal_expression(self, expr):
        raise NotImplementedError()

    @abc.abstractmethod
    def visit_unary_expression(self, expr):
        raise NotImplementedError()


class Expr(abc.ABC):

    def accept(self, visitor: Visitor):
        raise NotImplementedError()


@dataclasses.dataclass()
class BinaryExpr(Expr):
    left: Expr
    operator: Token
    right: Expr

    def accept(self, visitor: Visitor):
        return visitor.visit_binary_expression(self)


@dataclasses.dataclass()
class GroupingExpr(Expr):
    expression: Expr

    def accept(self, visitor: Visitor):
        return visitor.visit_grouping_expression(self)


@dataclasses.dataclass()
class LiteralExpr(Expr):
    value: str | int

    def accept(self, visitor: Visitor):
        return visitor.visit_literal_expression(self)


@dataclasses.dataclass()
class UnaryExpr(Expr):
    operator: Token
    right: Expr

    def accept(self, visitor: Visitor):
        return visitor.visit_unary_expression(self)


class Scanner:

    def __init__(self, source):
        self._source = source
        self._tokens = []

        self._start = 0
        self._current = 0

    @property
    def is_at_end(self):
        return self._current >= len(self._source)

    def scan_tokens(self):
        while not self.is_at_end and not self.peek() == '\n':
            self._start = self._current
            self.scan_token()

        self._tokens.append(Token(TokenType.EOF, '', None, self._start, self._current-1))
        return self._tokens

    def scan_token(self):
        c = self.advance()
        match c:
            case '+': self.add_token(TokenType.PLUS)
            case '-': self.add_token(TokenType.MINUS)
            case '*': self.add_token(TokenType.STAR)
            case '/': self.add_token(TokenType.SLASH)
            case '(': self.add_token(TokenType.LEFT_PAREN)
            case ')': self.add_token(TokenType.RIGHT_PAREN)
            case ' ': pass
            case _:
                if self.is_digit(c):
                    self.number()
                else:
                    raise ParseError(f'Unexpected character: {c} at position {self._current-1}.')

    def advance(self):
        c = self._source[self._current]
        self._current += 1
        return c

    def add_token(self, type, literal=None):
        lexeme = self._source[self._start:self._current]
        self._tokens.append(Token(type, lexeme, literal, self._start, self._current-1))

    def is_digit(self, c):
        return 48 <= ord(c) <= 57

    def number(self):
        while self.is_digit(self.peek()):
            self.advance()

        if self.peek() == '.' and self.is_digit(self.peek_next()):
            self.advance()

            while self.is_digit(self.peek()):
                self.advance()

        self.add_token(TokenType.NUMBER, float(self._source[self._start:self._current]))

    def peek(self):
        if self.is_at_end:
            return '\0'

        return self._source[self._current]

    def peek_next(self):
        if self._current + 1 >= len(self.source):
            return '\0'

        return self._source[self._current+1]


class Parser:
    '''
    expression     → term ;
    term           → factor ( ( "-" | "+" ) factor )* ;
    factor         → unary ( ( "/" | "*" ) unary )* ;
    unary          → "-" unary | primary ;
    primary        → NUMBER | "(" expression ")" ;
    '''

    def __init__(self, tokens):
        self._tokens = tokens
        self._current = 0

    def parse(self):
        return self.expression()

    def expression(self):
        return self.term()

    def term(self):
        expr = self.factor()

        while self.match([TokenType.MINUS, TokenType.PLUS]):
            operator = self.previous()
            right = self.factor()
            expr = BinaryExpr(expr, operator, right)

        return expr

    def factor(self):
        expr = self.unary()

        while self.match([TokenType.SLASH, TokenType.STAR]):
            operator = self.previous()
            right = self.unary()
            expr = BinaryExpr(expr, operator, right)

        return expr

    def unary(self):
        if self.match([TokenType.MINUS]):
            operator = self.previous()
            right = self.unary()
            expr = UnaryExpr(operator, right)
            return expr

        return self.primary()

    def primary(self):
        if self.match([TokenType.NUMBER]):
            value = self.previous().literal
            return LiteralExpr(value)

        if self.match([TokenType.LEFT_PAREN]):
            open_paren_token = self.previous()
            expr = self.expression()
            self.consume(TokenType.RIGHT_PAREN, f'Expect ")" after expression. The open paren was opened at position {open_paren_token.start_at}.')
            return GroupingExpr(expr)

        prev_token = self.previous()
        raise ParseError(f'Expect expression at position {prev_token.end_at} after "{prev_token.lexeme}".')

    def match(self, token_types):
        for ttype in token_types:
            if self.check(ttype):
                self.advance()
                return True

        return False

    def check(self, token_type):
        if self.is_at_end():
            return False

        return self.peek().type == token_type

    def advance(self):
        if not self.is_at_end():
            self._current += 1

        return self.previous()

    def is_at_end(self):
        return self.peek().type == TokenType.EOF

    def peek(self):
        return self._tokens[self._current]

    def previous(self):
        return self._tokens[self._current-1]

    def consume(self, token_type, message):
        if (self.check(token_type)):
            return self.advance()

        raise ParseError(message)


class Interpreter(Visitor):

    def evaluate(self, expr: Expr):
        return expr.accept(self)

    def visit_literal_expression(self, expr: LiteralExpr):
        return expr.value

    def visit_grouping_expression(self, expr: GroupingExpr):
        return self.evaluate(expr.expression)

    def visit_unary_expression(self, expr: UnaryExpr):
        right = self.evaluate(expr.right)

        if expr.operator.type is TokenType.MINUS:
            return -right

        return None

    def visit_binary_expression(self, expr: BinaryExpr):
        left = self.evaluate(expr.left)
        right = self.evaluate(expr.right)

        match expr.operator.type:
            case TokenType.PLUS: return left + right
            case TokenType.MINUS: return left - right
            case TokenType.SLASH: return left / right
            case TokenType.STAR: return left * right
            case _: return None

def get_source():
    with open('expression.txt', 'r') as f:
        return f.read()

if __name__ == '__main__':
    sys.setrecursionlimit(3000)
    source = get_source()

    try:
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()

        parser = Parser(tokens)
        expression = parser.parse()

        interpreter = Interpreter()
        value = interpreter.evaluate(expression)
        print(f'Result: {value:.2f}')
    except ParseError as exc:
        print(exc, file=sys.stderr)
        sys.exit(65)
