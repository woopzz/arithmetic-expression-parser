use std::fs;

#[derive(Debug)]
struct TokenType {
    uid: u8,
    precedence: u8,
}

impl PartialEq for TokenType {
    fn eq(&self, other: &Self) -> bool {
        self.uid == other.uid
    }
}

const UMINUS: TokenType = TokenType { uid: 1, precedence: 4 };
const STAR: TokenType = TokenType { uid: 2, precedence: 3 };
const SLASH: TokenType = TokenType { uid: 3, precedence: 3 };
const PLUS: TokenType = TokenType { uid: 4, precedence: 2 };
const MINUS: TokenType = TokenType { uid: 5, precedence: 2 };

const NUMBER: TokenType = TokenType { uid: 6, precedence: 0 };
const LEFT_PAREN: TokenType = TokenType { uid: 7, precedence: 0 };
const RIGHT_PAREN: TokenType = TokenType { uid: 8, precedence: 0 };

#[derive(Debug)]
struct Token {
    ttype: TokenType,
    lexeme: String,
    literal: Option<f64>,
    start_at: usize,
    end_at: usize,
}

struct Scanner {
    chars: Vec<char>,
    tokens: Vec<Token>,
    start: usize,
    current: usize,
}

impl Scanner {

    fn new(chars: Vec<char>) -> Self {
        Self {
            chars: chars,
            tokens: vec![],
            start: 0,
            current: 0,
        }
    }

    fn scan_tokens(&mut self) -> &Vec<Token> {
        while !self.is_at_end() && self.peek() != '\n' {
            self.start = self.current;
            self.scan_token();
        }

        return &self.tokens;
    }

    fn scan_token(&mut self) {
        let c = self.advance();
        match c {
            '+' => self.add_token(PLUS, None),
            '-' => {
                let tokens_count = self.tokens.len();
                if tokens_count < 1 || (
                    self.tokens[tokens_count-1].ttype != NUMBER &&
                    self.tokens[tokens_count-1].ttype != RIGHT_PAREN
                ) {
                    self.add_token(UMINUS, None);
                } else {
                    self.add_token(MINUS, None);
                }
            },
            '*' => self.add_token(STAR, None),
            '/' => self.add_token(SLASH, None),
            '(' => self.add_token(LEFT_PAREN, None),
            ')' => self.add_token(RIGHT_PAREN, None),
            _ => {
                if c == ' ' {
                    return;
                } if c.is_digit(10) {
                    self.number();
                } else {
                    panic!("Unexpected character: {} at position {}.", c, self.current-1);
                }
            },
        }
    }

    fn is_at_end(&self) -> bool {
        self.current >= self.chars.len()
    }

    fn advance(&mut self) -> char {
        let c = self.chars[self.current];
        self.current += 1;
        return c;
    }

    fn add_token(&mut self, ttype: TokenType, literal: Option<f64>) {
        self.tokens.push(Token {
            ttype: ttype,
            literal: literal,
            lexeme: self.make_lexeme(),
            start_at: self.start,
            end_at: self.current - 1,
        });
    }

    fn number(&mut self) {
        while self.peek().is_digit(10) {
            self.advance();
        }

        if self.peek() == '.' && self.peek_next().is_digit(10) {
            self.advance();

            while self.peek().is_digit(10) {
                self.advance();
            }
        }

        self.add_token(NUMBER, Some(self.get_float_number()));
    }

    fn peek(&self) -> char {
        if self.is_at_end() {
            return '\0';
        }

        return self.chars[self.current];
    }

    fn peek_next(&self) -> char {
        if self.current + 1 >= self.chars.len() {
            return '\0';
        }

        return self.chars[self.current+1]
    }

    // This way to make a substring is awful,
    // but I don't know how to do it in a better way.
    fn make_lexeme(&self) -> String {
        let mut string = String::new();
        for i in self.start..self.current {
            string.push(self.chars[i]);
        }
        return string;
    }

    fn get_float_number(&self) -> f64 {
        self.make_lexeme().parse::<f64>().unwrap()
    }

}

fn parse(tokens: &Vec<Token>) -> f64 {
    let mut current: usize = 0;
    let mut results: Vec<f64> = vec![];
    let mut operators: Vec<&Token> = vec![];

    let mut token: &Token;
    while current < tokens.len() {
        token = &tokens[current];
        current += 1;

        if token.ttype == NUMBER {
            let literal = match token.literal {
                Some(x) => x,
                None => unreachable!("Invalid number literal. Lexeme: {}.", token.lexeme),
            };
            results.push(literal);
        } else if token.ttype.precedence != 0 {
            while
                !operators.is_empty()
                && operators[operators.len()-1].ttype != LEFT_PAREN
                && operators[operators.len()-1].ttype.precedence >= token.ttype.precedence
            {
                let result = evaluate(operators.pop().unwrap(), &mut results);
                results.push(result);
            }
            operators.push(token);
        } else if token.ttype == LEFT_PAREN {
            operators.push(token);
        } else if token.ttype == RIGHT_PAREN {
            while !operators.is_empty() && operators[operators.len()-1].ttype != LEFT_PAREN {
                let result = evaluate(operators.pop().unwrap(), &mut results);
                results.push(result);
            }

            if operators.is_empty() {
                panic!("Mismatched right paren at position {}.", token.start_at);
            }

            operators.pop();
        }
    }

    while !operators.is_empty() {
        let operator = operators.pop().unwrap();
        if operator.ttype == LEFT_PAREN {
            panic!("Mismatched left paren at position {}.", operator.start_at);
        }

        let result = evaluate(operator, &mut results);
        results.push(result);
    }

    if results.len() != 1 {
        panic!("Cannot evaluate the expression to the concrete value.");
    }

    return results[0];
}

fn evaluate(operator: &Token, results: &mut Vec<f64>) -> f64 {
    let operand = results.pop().unwrap();

    if operator.ttype == PLUS {
        return results.pop().unwrap() + operand;
    }

    if operator.ttype == MINUS {
        return results.pop().unwrap() - operand;
    }

    if operator.ttype == UMINUS {
        return -operand;
    }

    if operator.ttype == STAR {
        return results.pop().unwrap() * operand;
    }

    if operator.ttype == SLASH {
        return results.pop().unwrap() / operand;
    }

    unreachable!("Invalid token type (at pos {}..{}) when an operator expected.", operator.start_at, operator.end_at);
}

fn get_source() -> String {
    match fs::read_to_string("expression.txt") {
        Err(why) => panic!("Couldn't read: {}", why),
        Ok(data) => data,
    }
}

fn main() {
    let source: String = get_source();

    let mut scanner = Scanner::new(source.chars().collect());
    let tokens = scanner.scan_tokens();

    // for token in tokens {
    //     println!("{:?}", token);
    // }

    println!("Result: {:.2}", parse(tokens));
}
