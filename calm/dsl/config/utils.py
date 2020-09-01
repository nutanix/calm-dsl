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
