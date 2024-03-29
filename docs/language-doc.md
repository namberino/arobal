# Arithmetic operations

AROBAL can support arithmetic operations. It also supports parentheses and knows which operations to prioritize.

```
AROBAL% 1 + 2 * 3
7
AROBAL% (1 + 2) * 3
9
```

There's built-in support for exponentiation.

```
AROBAL% 2 ^ 3
8
AROBAL% 2 ^ 1 + 3
5
```

There's also support for negative numbers

```
AROBAL% -5 + 2 * 3
1
```

___

# Variables

The `var` keyword is used to instantiate a variable.

```
AROBAL% var variable = 1
1
AROBAL% variable + 5
6
AROBAL% var variable = "hello world"
"hello world"
AROBAL% variable
"hello world"
```

___

# Strings

AROBAL can support strings and string operations

```
AROBAL% "hello world"
"hello world"
AROBAL% "hello " + "world"
"hello world"
AROBAL% "Hello" * 3
"HelloHelloHello"
```

___

# Lists

AROBAL has support for lists and list operations

```
AROBAL% [1, 2, 3, 4, 5]
[1, 2, 3, 4, 5]
AROBAL% [1, 2, 3] + 4
[1, 2, 3, 4]
AROBAL% [1, 2, 3] * [4, 5, 6]
[1, 2, 3, 4, 5, 6]
AROBAL% [1, 2, 3, 4, 5] - 1
[1, 3, 4, 5]
AROBAL% [1, 2, 3, 4, 5] - -2
[1, 2, 3, 5]
AROBAL% var random_nums = [3, 5, 9, 2, 4]
[3, 5, 9, 2, 4]
AROBAL% random_nums / 0
3
AROBAL% random_nums / 3
2
```

___

# Comparison operations

AROBAL can support comparison operations (`==`, `!=`, `>`, `<`, `>=`, `<=`)

```
AROBAL% 5 == 5
1
AROBAL% 5 != 5
0
AROBAL% 5 > 6
0
AROBAL% 5 < 6
1
AROBAL% 5 >= 5
1
AROBAL% 5 <= 4
0
```

___

# Logical operations

Currently, AROBAL supports 3 different logical operations: `not`, `and`, `or`

`and` operation:
```
AROBAL% 5 == 5 and 4 == 4
1
AROBAL% 5 == 5 and 4 == 5
0
```

`or` operation:
```
AROBAL% 5 == 5 or 4 == 4
1
AROBAL% 5 == 5 or 4 == 5
1
AROBAL% 5 == 4 or 4 == 5
0
```

`not` operation:
```
AROBAL% not 1
0
AROBAL% not 0
1
AROBAL% not 4
0
AROBAL% not -1
0
```

___

# Conditional statements

AROBAL has support for `if`, `elif` and `else` statements.

```
AROBAL% if age >= 19 then 2 elif age >= 18 then 1 else 0
1
AROBAL% if age >= 19 then 1 else 0
0
```

___

# Loops

AROBAL has support for both `for` loop and `while` loop.


`for` loop:
```
AROBAL% var x = 1
1
AROBAL% for i = 0 to 10 then var x = x + i
[1, 2, 4, 7, 11, 16, 22, 29, 37, 46]
```

`while` loop:
```
AROBAL% var x = 0
0
AROBAL% while x < 10 then var x = x + 1
[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
```

___

# Function

There's support for *functions* through the `function` keyword as well.

```
AROBAL% function power2(num) -> num * num
<function power2>
AROBAL% power2(2)
4
AROBAL% power2(5)
25
```

We can assign functions to variables.

```
AROBAL% var power2_function = power2
<function power2>
AROBAL% power2_function(6)
36
```

There's also support for *anonymous function*.

```
AROBAL% var anon_power2 = function (num) -> num * num
<function <anon>>
AROBAL% anon_power2(8)
64
```

___

