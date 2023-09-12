from calm.dsl.config.init_config import get_init_config_handle

init_config_handle = get_init_config_handle()
init_config_handle.update_init_config(
    config_file="./config.ini", db_file="./mock_dsl.db", local_dir="local"
)
