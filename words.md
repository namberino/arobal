# Some important vocabulary (Order by priority)

- function: KEYWORD FUNCTION identifier(optional) LPAREN identifier arguments(optional) RPAREN ARROW expression
- for expression: KEYWORD FOR identifier EQUAL expression KEYWORD TO expression KEYWORD STEP expression(optional) KEYWORD THEN expression
- while expression: KEYWORD WHILE expression KEYWORD THEN expression
- if expression:
  - KEYWORD IF expression KEYWORD THEN expression
  - KEYWORD ELIF expression KEYWORD THEN expression
  - KEYWORD ELSE expression
- Atom:
  - if expression
  - for expression
  - while expression
  - function
  - The numbers in the expression (int or float). 
  - Add support for parentheses here too (parentheses wrap around expression). 
  - Also add support for identifier (var name) here
- function call: Atom LPAREN expression arguments(optional) RPAREN
- Power: Atom ^ Factor
- Factor: Need to support negative numbers (unary operations) here.
- Term: Factor * or / Factor
- Arithmetic expression: Term + or - Term.
- Comparison expression: 
  - Arithmetic expression (EE, LT, GT, LTE, GTE) arithmetic expression
  - NOT comparison expression
- Expression: 
  - Comparison expression (KEYWORD: AND, OR) comparison expression
  - keyword VAR identifier(var_name) EQUAL expression

# Variables stuff
```
VAR         var_name        =    expression
 ^             ^            ^
KEYWORD    IDENTIFIER     EQUALS
```

This will be at the expression level
