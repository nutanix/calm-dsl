import importlib.util


def get_module_from_file(module_name, file):
    """Returns a module given a user python file (.py)"""

    spec = importlib.util.spec_from_file_location(module_name, file)
    user_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(user_module)

    return user_module
