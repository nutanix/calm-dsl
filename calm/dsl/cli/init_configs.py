import os
import errno


# TODO movet this method to calm.dsl.tools
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


def get_default_config_file():
    """Returns default location of config file"""

    user_config_file = os.path.join(os.path.expanduser("~"), ".calm", "config.ini")
    make_file_dir(user_config_file)
    return user_config_file


def get_default_db_file():
    """Returns default location of db file"""

    dsl_db_file = os.path.join(os.path.expanduser("~"), ".calm", "dsl.db")
    make_file_dir(dsl_db_file)
    return dsl_db_file


def get_default_local_dir():
    """Returns the default location for local dir"""

    local_dir = os.path.join(os.path.expanduser("~"), ".calm", ".local")
    make_file_dir(local_dir, is_dir=True)
    return local_dir
