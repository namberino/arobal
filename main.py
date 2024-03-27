import arobal

while True:
    text = input("AROBAL% ")
    result, error = arobal.run(text, "<stdin>")

    if error:
        print(error.as_string())
    else:
        print(result)
