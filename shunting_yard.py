import sys
import enum
import dataclasses


class ParseError(Exception):
    pass

# TokenType is not an enum anymore. Because we need a precedence for every operator.
# We can utilize zero precedence to distinguish operators from other token types.
@dataclasses.dataclass()
class TokenType:
    precedence: int

UMINUS = TokenType(4)
STAR = TokenType(3)
SLASH = TokenType(3)
PLUS = TokenType(2)
MINUS = TokenType(2)

NUMBER = TokenType(0)
LEFT_PAREN = TokenType(0)
RIGHT_PAREN = TokenType(0)


@dataclasses.dataclass()
class Token:
    type: TokenType
    literal: float | None
    start_at: int
    end_at: int


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
            case '+': self.add_token(PLUS)
            case '-':
                if (
                    not self._tokens or
                    (self._tokens[-1].type is not NUMBER and self._tokens[-1].type is not RIGHT_PAREN)
                ):
                    self.add_token(UMINUS)
                else:
                    self.add_token(MINUS)
            case '*': self.add_token(STAR)
            case '/': self.add_token(SLASH)
            case '(': self.add_token(LEFT_PAREN)
            case ')': self.add_token(RIGHT_PAREN)
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

        self.add_token(NUMBER, float(self._source[self._start:self._current]))

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

    while current < len(tokens):
        token = tokens[current]
        current += 1

        if token.type is NUMBER:
            output_queue.append(token.literal)
            continue

        if token.type.precedence:
            while (
                operators
                and operators[-1].type is not LEFT_PAREN
                and operators[-1].type.precedence >= token.type.precedence
            ):
                output_queue.append(evaluate(operators.pop(), output_queue))

            operators.append(token)

        if token.type is LEFT_PAREN:
            operators.append(token)
            continue

        if token.type is RIGHT_PAREN:
            while operators and operators[-1].type is not LEFT_PAREN:
                output_queue.append(evaluate(operators.pop(), output_queue))

            if not operators:
                raise ParseError(f'Mismatched right paren at position {token.start_at}.')

            operators.pop()

    while operators:
        operator = operators.pop()
        if operator.type is LEFT_PAREN:
            raise ParseError(f'Mismatched left paren at position {operator.start_at}.')

        output_queue.append(evaluate(operator, output_queue))

    if len(output_queue) != 1:
        raise ParseError('Cannot evaluate the expression to the concrete value.')

    return output_queue.pop()

def evaluate(token, output_queue):
    operand = output_queue.pop()
    if token.type is PLUS:
        return output_queue.pop() + operand
    if token.type is MINUS:
        return output_queue.pop() - operand
    if token.type is UMINUS:
        return -operand
    if token.type is STAR:
        return output_queue.pop() * operand
    if token.type is SLASH:
        return output_queue.pop() / operand

    raise ParseError(f'Invalid token type (at pos {token.start_at}..{token.end_at}) when an operator expected.')

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
