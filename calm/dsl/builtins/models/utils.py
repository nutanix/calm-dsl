import os
import sys
import inspect


def read_file(filename, depth=1):
    """reads the file"""

    file_path = os.path.join(
        os.path.dirname(inspect.getfile(sys._getframe(depth))), filename
    )

    with open(file_path, "r") as data:
        return data.read()
