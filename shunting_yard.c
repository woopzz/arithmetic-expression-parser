// clang -std=c99 -Wall -Werror -o shy shunting_yard.c
// DEBUG=1 ./shy expression.txt  # to run in debug mode
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define IS_DIGIT(value) ((value) >= '0' && (value) <= '9')
#define STACK_SIZE_SHY_OPERATORS 1024
#define STACK_SIZE_SHY_VALUES 1024

#define ERROR_INVALID_ARGS 1
#define ERROR_FILE_ERROR 2
#define ERROR_NOT_ENOUGH_MEMORY 3
#define ERROR_PARSING 4
#define ERROR_EVALUATION 5

typedef enum {
    TOKEN_UMINUS = 0,
    TOKEN_STAR,
    TOKEN_SLASH,
    TOKEN_PLUS,
    TOKEN_MINUS,
    TOKEN_NUMBER,
    TOKEN_LEFT_PAREN,
    TOKEN_RIGHT_PAREN,
    TOKEN_TYPE_COUNT
} TokenType;

static const int TOKEN_TYPE_PRECEDENCE[TOKEN_TYPE_COUNT] = {
    [TOKEN_UMINUS] = 4,

    [TOKEN_STAR] = 3,
    [TOKEN_SLASH] = 3,

    [TOKEN_PLUS] = 2,
    [TOKEN_MINUS] = 2,

    [TOKEN_NUMBER] = 0,
    [TOKEN_LEFT_PAREN] = 0,
    [TOKEN_RIGHT_PAREN] = 0,
};

typedef struct {
    TokenType type;
    double literal;
    int start_at;
    int end_at;
} Token;

typedef struct {
    Token *items;
    int count;
    int capacity;
} TokenList;

void token_list_init(TokenList *tl) {
    tl->items = NULL;
    tl->count = 0;
    tl->capacity = 0;
}

void token_list_add_item(TokenList *tl, Token t) {
    if (tl->count >= tl->capacity) {
        if (tl->capacity == 0) tl->capacity = 10;
        else tl->capacity *= 2;

        Token *items = realloc(tl->items, sizeof(Token) * tl->capacity);
        if (items == NULL) {
            fprintf(stderr, "Not enough memory for tokens.\n");
            exit(ERROR_NOT_ENOUGH_MEMORY);
        }

        tl->items = items;
    }
    tl->items[tl->count++] = t;
}

typedef struct {
    char *source;
    TokenList *tokens;
    int start;
    int current;
} Scanner;

void scanner_init(Scanner *scanner, char *source) {
    scanner->source = source;

    TokenList *tokens = malloc(sizeof(TokenList));
    token_list_init(tokens);
    scanner->tokens = tokens;

    scanner->start = 0;
    scanner->current = 0;
}

int scanner_is_at_end(Scanner *scanner) {
    char current = scanner->source[scanner->current];
    return current == '\0' || current == '\n';
}

char scanner_advance(Scanner *scanner) {
    char c = scanner->source[scanner->current];
    scanner->current++;
    return c;
}

void scanner_add_token(Scanner *scanner, TokenType type) {
    Token token;
    token.type = type;
    token.start_at = scanner->start;
    token.end_at = scanner->current - 1;
    token_list_add_item(scanner->tokens, token);
}

char scanner_peek(Scanner *scanner) {
    return scanner->source[scanner->current];
}

char scanner_peek_next(Scanner *scanner) {
    if (scanner_peek(scanner) == '\0') {
        return '\0';
    }
    return scanner->source[scanner->current + 1];
}

void scanner_number(Scanner *scanner) {
    while (IS_DIGIT(scanner_peek(scanner))) scanner_advance(scanner);

    if (scanner_peek(scanner) == '.' && IS_DIGIT(scanner_peek_next(scanner))) {
        scanner_advance(scanner);
        while (IS_DIGIT(scanner_peek(scanner))) scanner_advance(scanner);
    }

    scanner_add_token(scanner, TOKEN_NUMBER);

    Token *token = &scanner->tokens->items[scanner->tokens->count-1];
    int start_at = token->start_at;
    int end_at = token->start_at + 1;
    int length = end_at - start_at + 2;

    char liter_as_str[length];
    memcpy(liter_as_str, &(scanner->source[start_at]), sizeof(char) * (length - 1));
    liter_as_str[length-1] = '\0';

    double literal = atof(liter_as_str);
    token->literal = literal;
}

void scanner_scan_token(Scanner *scanner) {
    char c = scanner_advance(scanner);
    switch (c) {
        case '+': scanner_add_token(scanner, TOKEN_PLUS); break;
        case '-': {
            TokenList *tokens = scanner->tokens;
            if (
                tokens->count == 0
                || (
                    tokens->items[tokens->count-1].type != TOKEN_NUMBER
                    && tokens->items[tokens->count-1].type != TOKEN_RIGHT_PAREN
                )
            ) {
                scanner_add_token(scanner, TOKEN_UMINUS);
            } else {
                scanner_add_token(scanner, TOKEN_MINUS);
            }
            break;
        };
        case '*': scanner_add_token(scanner, TOKEN_STAR); break;
        case '/': scanner_add_token(scanner, TOKEN_SLASH); break;
        case '(': scanner_add_token(scanner, TOKEN_LEFT_PAREN); break;
        case ')': scanner_add_token(scanner, TOKEN_RIGHT_PAREN); break;
        case ' ': break;
        default: {
            if (IS_DIGIT(c)) {
                scanner_number(scanner);
            } else {
                fprintf(stderr, "Unexpected character: %c at position %d.", c, scanner->current - 1);
                exit(ERROR_PARSING);
            }
        }
    }
}

TokenList* scanner_execute(Scanner *scanner) {
    while (!scanner_is_at_end(scanner)) {
        scanner->start = scanner->current;
        scanner_scan_token(scanner);
    }
    return scanner->tokens;
}

Token shy_operators[STACK_SIZE_SHY_OPERATORS];
int shy_operators_count = 0;

void push_operator(Token token) {
    if (shy_operators_count >= STACK_SIZE_SHY_OPERATORS) {
        fprintf(stderr, "Operators stack is overflowed.");
        exit(ERROR_EVALUATION);
    }
    shy_operators[shy_operators_count++] = token;
}

Token peek_operator() {
    if (shy_operators_count <= 0) {
        fprintf(stderr, "Operators stack is empty.");
        exit(ERROR_EVALUATION);
    }
    return shy_operators[shy_operators_count - 1];
}

Token pop_operator() {
    Token token = peek_operator();
    shy_operators_count--;
    return token;
}

double shy_values[STACK_SIZE_SHY_VALUES];
int shy_values_count = 0;

void push_value(double value) {
    if (shy_values_count >= STACK_SIZE_SHY_VALUES) {
        fprintf(stderr, "Values stack is overflowed.");
        exit(ERROR_EVALUATION);
    }
    shy_values[shy_values_count++] = value;
}

double pop_value() {
    if (shy_values_count <= 0) {
        fprintf(stderr, "Values stack is empty.");
        exit(ERROR_EVALUATION);
    }
    return shy_values[--shy_values_count];
}

double evaluate(Token operator) {
    double operand = pop_value();
    switch (operator.type) {
        case TOKEN_PLUS: return pop_value() + operand;
        case TOKEN_MINUS: return pop_value() - operand;
        case TOKEN_UMINUS: return -operand;
        case TOKEN_STAR: return pop_value() * operand;
        case TOKEN_SLASH: return pop_value() / operand;
        default: {
            fprintf(
                stderr, "Invalid token type (at pos %d..%d) when an operator expected.",
                operator.start_at, operator.end_at
            );
            exit(ERROR_EVALUATION);
        };
    }
}

double eval_by_shunting_yard(TokenList *tokens) {
    int current = 0;
    int total = tokens->count;
    while (current < total) {
        Token token = tokens->items[current++];

        if (token.type == TOKEN_NUMBER) {
            push_value(token.literal);
            continue;
        }

        int precedence = TOKEN_TYPE_PRECEDENCE[token.type];
        if (precedence > 0) {
            while (
                shy_operators_count > 0
                && peek_operator().type != TOKEN_LEFT_PAREN
                && TOKEN_TYPE_PRECEDENCE[peek_operator().type] >= precedence
            ) {
                push_value(evaluate(pop_operator()));
            }

            push_operator(token);
        }

        if (token.type == TOKEN_LEFT_PAREN) {
            push_operator(token);
            continue;
        }

        if (token.type == TOKEN_RIGHT_PAREN) {
            while (
                shy_operators_count > 0
                && peek_operator().type != TOKEN_LEFT_PAREN
            ) {
                push_value(evaluate(pop_operator()));
            }

            if (shy_operators_count == 0) {
                fprintf(stderr, "Mismatched right paren at position %d.", token.start_at);
                exit(ERROR_EVALUATION);
            }

            pop_operator();
        }
    }

    while (shy_operators_count > 0) {
        Token operator = pop_operator();
        if (operator.type == TOKEN_LEFT_PAREN) {
            fprintf(stderr, "Mismatched left paren at position %d.", operator.start_at);
            exit(ERROR_EVALUATION);
        }

        push_value(evaluate(operator));
    }

    if (shy_values_count != 1) {
        fprintf(stderr, "Cannot evaluate the expression to the concrete value.");
        exit(ERROR_EVALUATION);
    }

    return pop_value();
}

char* read_file(const char *path) {
    FILE *file = fopen(path, "rb");
    if (file == NULL) {
        fprintf(stderr, "Could not open file \"%s\".\n", path);
        exit(ERROR_FILE_ERROR);
    }

    fseek(file, 0L, SEEK_END);
    size_t fileSize = ftell(file);
    rewind(file);

    char *buffer = malloc(fileSize + 1);
    if (buffer == NULL) {
        fprintf(stderr, "Not enough memory to read \"%s\".\n", path);
        exit(ERROR_NOT_ENOUGH_MEMORY);
    }

    size_t bytesRead = fread(buffer, sizeof(char), fileSize, file);
    if (bytesRead < fileSize) {
        fprintf(stderr, "Could not read file \"%s\".\n", path);
        exit(ERROR_FILE_ERROR);
    }

    buffer[bytesRead] = '\0';

    fclose(file);
    return buffer;
}

void process_file(const char *path, int print_debug_info) {
    char *source = read_file(path);
    if (print_debug_info) {
        printf("File content: %s", source);
    }

    Scanner scanner;
    scanner_init(&scanner, source);
    TokenList *tokens = scanner_execute(&scanner);

    if (print_debug_info) {
        printf("Tokens:\n");
        for (int i = 0; i < tokens->count; i++) {
            Token *token = &tokens->items[i];
            printf("[%d] type = %d, start at = %d, end at = %d", i, token->type, token->start_at, token->end_at);
            if (token->type == TOKEN_NUMBER) {
                printf(", literal = %.2f", token->literal);
            }
            printf("\n");
        }
    }

    free(source);

    double result = eval_by_shunting_yard(tokens);
    printf("Result: %.2f\n", result);

    free(tokens->items);
}

int main(int argc, char **argv) {
    int debug = getenv("DEBUG") != NULL;
    if (debug) {
        printf("[Debug enabled]\n");
    }

    if (argc == 2) {
        process_file(argv[1], debug);
    } else {
        fprintf(stderr, "Usage: shy [path]\n");
        exit(ERROR_INVALID_ARGS);
    }
    return 0;
}
