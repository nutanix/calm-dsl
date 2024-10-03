import types
from .decompile_helpers import process_variable_name

SERVICE_NAME_MAP = {}
PROFILE_NAME_MAP = {}
ENTITY_GUI_DSL_NAME_MAP = {}
PACKAGE_NAME_MAP = {}
DEPLOYMENT_NAME_MAP = {}
POWER_ACTION_SUBSTRATE_MAP = {}
RESOURCE_TYPE_NAME_MAP = {}
ENDPOINT_NAME_MAP = {}


def get_service_name(name):
    """returns the class name used for entity ref"""

    global SERVICE_NAME_MAP
    return SERVICE_NAME_MAP.get(name, None)


def update_service_name(ui_name, dsl_name):
    """updates the ui and dsl name mapping"""

    global SERVICE_NAME_MAP
    SERVICE_NAME_MAP[ui_name] = dsl_name


def get_profile_name(name):
    """returns the class name used for entity ref"""

    global PROFILE_NAME_MAP
    return PROFILE_NAME_MAP.get(name, None)


def update_profile_name(ui_name, dsl_name):

    global PROFILE_NAME_MAP
    PROFILE_NAME_MAP[ui_name] = dsl_name


def get_resource_type_name(name):
    """returns the class name used for entity ref"""

    global RESOURCE_TYPE_NAME_MAP
    return RESOURCE_TYPE_NAME_MAP.get(name, None)


def update_resource_type_name(ui_name, dsl_name):

    global RESOURCE_TYPE_NAME_MAP
    RESOURCE_TYPE_NAME_MAP[ui_name] = dsl_name


def get_entity_gui_dsl_name(ui_name):

    global ENTITY_GUI_DSL_NAME_MAP
    return ENTITY_GUI_DSL_NAME_MAP.get(ui_name, None)


def update_entity_gui_dsl_name(ui_name, dsl_name):

    global ENTITY_GUI_DSL_NAME_MAP
    ENTITY_GUI_DSL_NAME_MAP[ui_name] = dsl_name


def get_package_name(name):
    """returns the class name used for entity ref"""

    global PACKAGE_NAME_MAP
    return PACKAGE_NAME_MAP.get(name, None)


def update_package_name(ui_name, dsl_name):

    global PACKAGE_NAME_MAP
    PACKAGE_NAME_MAP[ui_name] = dsl_name


def update_endpoint_name(ui_name, dsl_name):
    global ENDPOINT_NAME_MAP
    ENDPOINT_NAME_MAP[ui_name] = dsl_name


def get_endpoint_name(name):
    global ENDPOINT_NAME_MAP
    return ENDPOINT_NAME_MAP.get(name, None)


def get_deployment_name(name):
    """returns the class name used for entity ref"""

    global DEPLOYMENT_NAME_MAP
    return DEPLOYMENT_NAME_MAP.get(name, None)


def update_deployment_name(ui_name, dsl_name):

    global DEPLOYMENT_NAME_MAP
    DEPLOYMENT_NAME_MAP[ui_name] = dsl_name


def get_power_action_target_substrate(runbook_name):
    """returns the substrate name used for power action runbook"""

    global POWER_ACTION_SUBSTRATE_MAP
    return POWER_ACTION_SUBSTRATE_MAP.get(runbook_name, None)


def get_power_action_substrate_map():
    global POWER_ACTION_SUBSTRATE_MAP

    # returning immutable proxy of dict to prevent modification of original dict.
    return types.MappingProxyType(POWER_ACTION_SUBSTRATE_MAP)


def update_power_action_target_substrate(runbook_name, substrate_name):
    """updates power action runbook name to substrate name mapping"""

    global POWER_ACTION_SUBSTRATE_MAP
    POWER_ACTION_SUBSTRATE_MAP[runbook_name] = substrate_name


def init_ref_dependency_globals():

    global SERVICE_NAME_MAP, PROFILE_NAME_MAP, ENTITY_GUI_DSL_NAME_MAP, ENDPOINT_NAME_MAP
    global PACKAGE_NAME_MAP, DEPLOYMENT_NAME_MAP, POWER_ACTION_SUBSTRATE_MAP, RESOURCE_TYPE_NAME_MAP

    SERVICE_NAME_MAP = {}
    PROFILE_NAME_MAP = {}
    ENTITY_GUI_DSL_NAME_MAP = {}
    PACKAGE_NAME_MAP = {}
    DEPLOYMENT_NAME_MAP = {}
    POWER_ACTION_SUBSTRATE_MAP = {}
    RESOURCE_TYPE_NAME_MAP = {}
    ENDPOINT_NAME_MAP = {}
