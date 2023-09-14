import sys
import os
from calm.dsl.config.init_config import get_init_config_handle


def mock_init_config(config_location, db_location, local_dir):
    """
    updates init.ini with provided config, db and local dir location.
    config, db and local dir location should be provider with reference to root dir.
    """
    init_config_handle = get_init_config_handle()
    root_directory = os.path.expanduser("~")
    config_location = os.path.join(root_directory, config_location)
    db_location = os.path.join(root_directory, db_location)
    local_dir = os.path.join(root_directory, local_dir)

    init_config_handle.update_init_config(
        config_file=config_location, db_file=db_location, local_dir=local_dir
    )


def mock_context_config():
    pass


if __name__ == "__main__":
    if len(sys.argv) == 4:
        config_location = sys.argv[1]
        db_location = sys.argv[2]
        local_dir = sys.argv[3]
    else:
        config_location = ".calm/config.ini"
        db_location = ".calm/dsl.db"
        local_dir = ".calm/.local"

    mock_init_config(config_location, db_location, local_dir)
