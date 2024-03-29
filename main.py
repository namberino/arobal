import arobal

while True:
    text = input("AROBAL% ")
    if text.strip() == "":
        continue
    result, error = arobal.run(text, "<stdin>")

    if error:
        print(error.as_string())
    elif result:
        if len(result.elements) == 1:
            print(repr(result.elements[0]))
        else:
            print(repr(result))
