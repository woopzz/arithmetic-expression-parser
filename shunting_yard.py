import sys
import enum
import dataclasses


class ParseError(Exception):
    pass


class TokenType(enum.Enum):
    NUMBER = enum.auto()
    PLUS = enum.auto()
    MINUS = enum.auto()
    UMINUS = enum.auto()
    STAR = enum.auto()
    SLASH = enum.auto()
    LEFT_PAREN = enum.auto()
    RIGHT_PAREN = enum.auto()


@dataclasses.dataclass()
class Token:
    type: TokenType
    literal: float | None
    start_at: int
    end_at: int


OPERATOR_TOKEN_TYPE_TO_PRECEDENCE = {
    TokenType.PLUS: 2,
    TokenType.MINUS: 2,
    TokenType.UMINUS: 4,
    TokenType.STAR: 3,
    TokenType.SLASH: 3,
}


# It is a copy from "recursive_descent.py".
# ---
# But there are both the unary minus and the binary minus.
# It is important to distinguish them at this stage, because the shunting yard algorithm needs this info.
# ---
# And without EOF. I do not really understand the use of it.
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
        while not self.is_at_end and self.peek() != '\n':
            self._start = self._current
            self.scan_token()

        return self._tokens

    def scan_token(self):
        c = self.advance()
        match c:
            case '+': self.addToken(TokenType.PLUS)
            case '-': self.addToken(TokenType.MINUS)
            case '*': self.addToken(TokenType.STAR)
            case '/': self.addToken(TokenType.SLASH)
            case '(': self.addToken(TokenType.LEFT_PAREN)
            case ')': self.addToken(TokenType.RIGHT_PAREN)
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

    def addToken(self, type, literal=None):
        self._tokens.append(Token(type, literal, self._start, self._current-1))

    def is_digit(self, c):
        return 48 <= ord(c) <= 57

    def number(self):
        while self.is_digit(self.peek()):
            self.advance()

        if self.peek() == '.' and self.is_digit(self.peek_next()):
            self.advance()

            while self.is_digit(self.peek()):
                self.advance()

        self.addToken(TokenType.NUMBER, float(self._source[self._start:self._current]))

    def peek(self):
        if self.is_at_end:
            return '\0'

        return self._source[self._current]

    def peek_next(self):
        if self._current + 1 >= len(self.source):
            return '\0'

        return self._source[self._current+1]

def parse(tokens):
    current = 0
    output_queue = []
    operators = []

    operator_token_types = set(OPERATOR_TOKEN_TYPE_TO_PRECEDENCE.keys())

    while current < len(tokens):
        token = tokens[current]
        current += 1

        if token.type is TokenType.NUMBER:
            output_queue.append(token.literal)
            continue

        if token.type in operator_token_types:
            while (
                operators
                and operators[-1].type is not TokenType.LEFT_PAREN
                and OPERATOR_TOKEN_TYPE_TO_PRECEDENCE[operators[-1].type] >= OPERATOR_TOKEN_TYPE_TO_PRECEDENCE[token.type]
            ):
                output_queue.append(evaluate(operators.pop(), output_queue))

            operators.append(token)

        if token.type is TokenType.LEFT_PAREN:
            operators.append(token)
            continue

        if token.type is TokenType.RIGHT_PAREN:
            while operators and operators[-1].type is not TokenType.LEFT_PAREN:
                output_queue.append(evaluate(operators.pop(), output_queue))

            if not operators:
                raise ParseError(f'Mismatched right paren at position {token.start_at}.')

            operators.pop()

    while operators:
        operator = operators.pop()
        if operator.type is TokenType.LEFT_PAREN:
            raise ParseError(f'Mismatched left paren at position {operator.start_at}.')

        output_queue.append(evaluate(operator, output_queue))

    if len(output_queue) != 1:
        raise ParseError('Cannot evaluate the expression to the concrete value.')

    return output_queue.pop()

def evaluate(token, output_queue):
    operand = output_queue.pop()
    match token.type:
        case TokenType.PLUS: return output_queue.pop() + operand
        case TokenType.MINUS: return output_queue.pop() - operand
        case TokenType.UMINUS: return -operand
        case TokenType.STAR: return output_queue.pop() * operand
        case TokenType.SLASH: return output_queue.pop() / operand
        case _: raise ParseError(f'Invalid token type (at pos {token.start_at}..{token.end_at}) when an operator expected.')

def get_source():
    with open('expression.txt', 'r') as f:
        return f.read()

if __name__ == '__main__':
    source = get_source()

    try:
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()

        value = parse(tokens)
        print(f'Result: {value:.2f}')
    except ParseError as exc:
        print(exc, file=sys.stderr)
        sys.exit(65)
