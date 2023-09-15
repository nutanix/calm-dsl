import sys
import os
from calm.dsl.config import set_dsl_config
from constants import MockConstants


def mock_init_config(config_location, db_location, local_dir):
    """
    updates init.ini with provided config, db and local dir location.
    config, db and local dir location should be provider with reference to root dir.
    """
    root_directory = os.path.expanduser("~")
    config_location = os.path.join(root_directory, config_location)
    db_location = os.path.join(root_directory, db_location)
    local_dir = os.path.join(root_directory, local_dir)

    set_dsl_config(
        host=MockConstants.dsl_context.get("host", None),
        port=MockConstants.dsl_context.get("port", None),
        username=MockConstants.dsl_context.get("username", None),
        password=MockConstants.dsl_context.get("password", None),
        project_name=MockConstants.dsl_context.get("project_name", None),
        log_level=MockConstants.dsl_context.get("log_level", None),
        db_location=db_location,
        local_dir=local_dir,
        config_file=config_location,
        policy_status=MockConstants.dsl_context.get("policy_status", None),
        approval_policy_status=MockConstants.dsl_context.get(
            "approval_policy_status", None
        ),
        stratos_status=MockConstants.dsl_context.get("stratos_status", None),
        retries_enabled=MockConstants.dsl_context.get("retries_enabled", None),
        connection_timeout=MockConstants.dsl_context.get("connection_timeout", None),
        read_timeout=MockConstants.dsl_context.get("read_timeout", None),
    )


def mock_context_config():
    pass


if __name__ == "__main__":

    mock_config_update = False

    if len(sys.argv) > 1:
        mock_config_update = sys.argv[1]
        mock_config_update = True if mock_config_update == "True" else False

    if mock_config_update:
        config_location = ".calm/mock/config.ini"
        db_location = ".calm/mock/dsl.db"
        local_dir = ".calm/mock/.local"

        mock_init_config(config_location, db_location, local_dir)
