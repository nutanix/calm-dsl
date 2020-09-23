import importlib.util
import os
import errno


def make_file_dir(path, is_dir=False):
    """creates the file directory if not present"""

    # Create parent directory if not present
    if not os.path.exists(os.path.dirname(os.path.realpath(path))):
        try:
            os.makedirs(os.path.dirname(os.path.realpath(path)))

        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise Exception("[{}] - {}".format(exc["code"], exc["error"]))

    if is_dir and (not os.path.exists(path)):
        os.makedirs(path)


def get_module_from_file(module_name, file):
    """Returns a module given a user python file (.py)"""

    spec = importlib.util.spec_from_file_location(module_name, file)
    user_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(user_module)

    return user_module
