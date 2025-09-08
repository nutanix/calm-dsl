# python3;failure
def greet(name):
    print(f"Hello, {name}!")
def add(a, b):
    return a + b
def buggy_function():
    return 10 / 0  # ZeroDivisionError
def main():
    greet("Escript")
    result = add(5, 3)
    print("The result is:", result)
    buggy_function()  # This will raise a ZeroDivisionError
    # Error on this line (line 10)
    print(undefined_variable)  # NameError: name 'undefined_variable' is not defined
main()