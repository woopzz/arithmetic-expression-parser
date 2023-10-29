import os
import operator

SUPPORTED_OPERATORS_MAP = {
    '+': operator.add,
    '-': operator.sub,
}

def calculate(expression):
    '''
    Evaluates the expression which must be a string and returns a number as a result.
    '''
    stacks = [[]]
    digits = []

    def check_digits():
        nonlocal digits
        if digits:
            number_str = ''.join(digits)
            stacks[-1].append(int(number_str))
            digits = []

    def process(stack):
        stack.reverse()
        while len(stack) > 1:

            el = stack.pop()

            # Binary operator way ...
            if isinstance(el, int):

                fst_operand = el

                operator = stack.pop()
                if operator not in SUPPORTED_OPERATORS_MAP:
                    raise Exception('An operator is expected.')

                if not stack:
                    raise Exception('Invalid expression: {} {} what?'.format(fst_operand, operator))

                snd_operand = stack.pop()
                if not isinstance(snd_operand, int):
                    raise Exception('It must be the second operand: {}.'.format(snd_operand))

                res = SUPPORTED_OPERATORS_MAP[operator](fst_operand, snd_operand)
                stack.append(res)

            # Unary operator way ...
            elif el in SUPPORTED_OPERATORS_MAP:

                operator = el

                operand = stack.pop()
                if not isinstance(operand, int):
                    raise Exception('It must be an operand: {}.'.format(operand))

                res = SUPPORTED_OPERATORS_MAP[operator](0, operand)
                stack.append(res)

            else:
                raise Exception('Invalid expression.')

        if len(stack) != 1:
            raise Exception('Invalid expression.')

        return stack[0]

    for symbol in expression.strip('\n'):

        if symbol.isnumeric():
            digits += symbol
            continue
        check_digits()

        if symbol == '(':
            stacks.append([])
            continue

        if symbol == ')':
            result_of_last_stack_computation = process(stacks.pop())
            stacks[-1].append(result_of_last_stack_computation)
            continue

        if symbol in SUPPORTED_OPERATORS_MAP:
            stacks[-1].append(symbol)
        else:
            raise Exception('Invalid operator! You\'re allowed to use +-') from None

    check_digits()
    process(stacks[-1])

    if len(stacks) != 1:
        raise Exception('Invalid expression.')

    if len(stacks[0]) != 1:
        raise Exception('Invalid expression.')

    return stacks[0][0]

def retrieve_expr_from_file(file_path):
    '''
    Returns the content of a file with file_path.
    '''
    if not os.path.isfile(file_path):
        raise Exception('You must have expression.txt which contains an expression string in the same folder with this script.')

    expression = False
    with open(file_path, 'r') as file:
        expression = file.read()

    if not expression:
        raise Exception('What do you keep in expression.txt?')

    return expression

if __name__ == '__main__':
    expression = retrieve_expr_from_file('./expression.txt')
    expr_result = calculate(expression)
    print('Result:', expr_result)
