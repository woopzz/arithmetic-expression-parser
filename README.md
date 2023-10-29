# An arithmetic expression parser

So we have [a one-line expression](./expression.txt). We want to know the result.

<details>
<summary>Actually, I already know ...</summary>-56
</details>

---

*Some implementations support multiplication and division. Although these operations are not presented in the expression.*

### First take

A straightforward approach was to care only about digits (compose them into numbers) and the operators (plus and minus). But it did not work because a minus before an expression, that is set off by parentheses, toggles all signs inside the expression. Although it worked well for simpler expressions without parens. So the problem could be solved by processing parenthetical expressions independently and then just replaced them on the result.

---

Thus, there is a stack for every "group". When a left paren appears, a new stack is created and all following items go there, until a right paren occurs. Then the expression within the current stack is evaluated and the result goes to the previous stack.

`1+(2+(3+4))`

| First stack | Second stack | Third stack |
| ----------- | ------------ | ----------- |
| 1 | | |
| 1+ | | |
| 1+ | 2 | |
| 1+ | 2+ | |
| 1+ | 2+ | 3 |
| 1+ | 2+ | 3+ |
| 1+ | 2+ | 3+4 |
| 1+ | 2+ | 7 |
| 1+ | 2+7 | |
| 1+ | 9 | |
| 1+9 | | |
| 10 | | |

[Python](./stack_per_parenthetical_expression.py)

### Second take

Several years later, I discovered [Crafting Interpreters](https://craftinginterpreters.com/contents.html). And decided to adapt the first example from the book (up to the chapter 7) to evaluate the expression.

Some differences:
- Accepts only one line. The parser stops when it consumes "\n".
- The AST node generator is ommited. Not worth it in my case.
- Fail-fast. I'm not bothered by getting errors one-by-one in this case.
- Different error messages. Because it accepts only one line, there is no need to store a line number. Instead, start & end column numbers are stored. When an error occurs, these numbers are used in the error message.
- No checking that operands are numbers. All valid expressions boil down to numbers so, if I get it right, such situation cannot occur.

Important! It exceeds the Python default recursion limit (`1000` for the interpreter on my machine). Hence `sys.setrecursionlimit(3000)`. It works for me. But there are some caveats about changing the recursion limit. [Check this thread.](https://stackoverflow.com/questions/3323001/what-is-the-maximum-recursion-depth-and-how-to-increase-it)

[Python](./recursive_descent.py)

### Third take

*[Guido does not want the tail recursion in Python](https://neopythonic.blogspot.com/2009/04/final-words-on-tail-calls.html). So we have a huge call stack without optimizations.*

I wondered about a simple but iterative algorithm. And I found it [here](https://eli.thegreenplace.net/2009/03/20/a-recursive-descent-parser-with-an-infix-expression-evaluator/). The shunting yard algorithm uses two stacks: operands and values. And no recursion. The implementation is easy in my case. I just rewrote on Python [the example from Wikipedia](https://en.wikipedia.org/wiki/Shunting_yard_algorithm#The_algorithm_in_detail).

*There are several more articles about parsers in the blog. E.g. the algorithm J.B. mentioned in the video. Unfortunately, they are not compiled in a series. You should search for them through the archive.*

[Python](./shunting_yard.py)

*By the way, there is [an intresting video with Jonathan Blow and Casey Muratori](https://www.youtube.com/watch?v=MnctEW1oL-E&lc=UgyXFRaTPpT7E0R09Nh4AaABAg&t=4080). Also there is a cool comment (if you go by the link, it should be "highlighted"; basically, it should be the first one). I did not use that algorithm because it is also recursive.*
