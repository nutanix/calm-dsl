import sys
from calm.dsl.tools import get_logging_handle

LOG = get_logging_handle(__name__)
UI_DSL_NAME_MAP = {}


# Limited to names for service/package/deployment/profile/substrate/VM_name
# TODO enhance it for variable and action names also
def add_ui_dsl_name_map_entry(ui_name, dsl_name):
    global UI_DSL_NAME_MAP

    if UI_DSL_NAME_MAP.get(ui_name, None):
        LOG.error("Multiple entities with same name '{}' found".format(ui_name))
        sys.exit(-1)

    UI_DSL_NAME_MAP[ui_name] = dsl_name


def get_ui_dsl_name_map():
    global UI_DSL_NAME_MAP
    return UI_DSL_NAME_MAP


def update_ui_dsl_name_map_(updated_map):
    global UI_DSL_NAME_MAP
    if updated_map and isinstance(updated_map, dict):
        UI_DSL_NAME_MAP = updated_map
