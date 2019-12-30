from calm.dsl.config import get_config_file


def print_config():

    config_file = get_config_file()
    with open(config_file) as fd:
        print(fd.read())
