import basic

while True:
    text = input("NAMBASIC > ")
    result, error = basic.run(text, "stdin")

    if error:
        print(error.as_string())
    else:
        print(result)
