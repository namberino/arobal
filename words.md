# Some important vocabulary (Order by priority)

- Atom: The numbers in the expression (int or float). Add support for parentheses here too (parentheses wrap around expression). Also add support for identifier (var name) here
- Power: Atom ^ Factor
- Factor: Need to support negative numbers (unary operations) here.
- Term: Factor * or / Factor
- Expression: Term + or - Term.

# Variables stuff
```
VAR         var_name        =    expression
 ^             ^            ^
KEYWORD    IDENTIFIER     EQUALS
```

This will be at the expression level

Structure: keyword VAR identifier(var_name) EQUAL expression
