# An arithmetic expression parser

So we have [a one-line expression](./expression.txt).

### First take

Because all operations (except the grouping) have the same precedence, we can just pop both operands and an operator, then perform an operation.
To support the grouping by parenthesis, we have a stack for every "group". When an open bracket appears, we create a new stack and put all following items there,
until we get a closing bracket; then we evaluate the expression within the current stack and put the result into the previous stack. One stack per group, but it can be nested e.g. a stack contains a stack which is contains a stack ... `1+(2+(3+4))`.

Pretty dumb implementation but it works. I'm sure it can be solved in a more elegant way ... with a smart traversing by several pointers ... and without all these nested stacks.

[Python](./stack_per_embraced_expression.py)

### Second take

Several years later, I discovered [Crafting Interpreters](https://craftinginterpreters.com/contents.html). And decided to adapt the first example from the book (up to the chapter 7) to evaluate the expression.

Some differences:
- Accept only one line. The parser stops when it consumes "\n".
- The AST node generator is ommited. Not worth it in my case.
- Fail-fast. I'm not bothered by getting errors one-by-one in this case.
- Different error handling. Because we accept only one line, there is no need to store a line number. Instead, start & end column numbers are stored. When an error occurs, these numbers are used in the error message.
- No checking that operands are numbers. All valid expressions boil down to numbers so, if I get it right, such situation cannot occur.

Important! It exceeds the Python default recursion limit (`1000` for the interpreter on my machine). Hence `sys.setrecursionlimit(3000)`. It works for me. But there are some caveats about changing the recursion limit. [Check this thread.](https://stackoverflow.com/questions/3323001/what-is-the-maximum-recursion-depth-and-how-to-increase-it)

[Python](./recursive_descent.py)
