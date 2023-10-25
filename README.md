# An arithmetic expression parser

So we have [a one-line expression](./expression.txt).

### First take

Because all operations (except the grouping) have the same precedence, we can just pop both operands and an operator, then perform an operation.
To support the grouping by parenthesis, we have a stack for every "group". When an open bracket appears, we create a new stack and put all following items there,
until we get a closing bracket; then we evaluate the expression within the current stack and put the result into the previous stack. One stack per group, but it can be nested e.g. a stack contains a stack which is contains a stack ... `1+(2+(3+4))`.

Pretty dumb implementation but it works. I'm sure it can be solved in a more elegant way ... with a smart traversing by several pointers ... and without all these nested stacks.

[Python](./stack_per_embraced_expression.py)
