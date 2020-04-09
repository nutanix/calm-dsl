SERVICE_NAME_MAP = {}
PROFILE_NAME_MAP = {}
SUBSTRATE_NAME_MAP = {}
PACKAGE_NAME_MAP = {}
DEPLOYMENT_NAME_MAP = {}


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


def get_substrate_name(name):
    """returns the class name used for entity ref"""

    global SUBSTRATE_NAME_MAP
    return SUBSTRATE_NAME_MAP.get(name, None)


def update_substrate_name(ui_name, dsl_name):

    global SUBSTRATE_NAME_MAP
    SUBSTRATE_NAME_MAP[ui_name] = dsl_name


def get_package_name(name):
    """returns the class name used for entity ref"""

    global PACKAGE_NAME_MAP
    return PACKAGE_NAME_MAP.get(name, None)


def update_package_name(ui_name, dsl_name):

    global PACKAGE_NAME_MAP
    PACKAGE_NAME_MAP[ui_name] = dsl_name


def get_deployment_name(name):
    """returns the class name used for entity ref"""

    global DEPLOYMENT_NAME_MAP
    return DEPLOYMENT_NAME_MAP.get(name, None)


def update_deployment_name(ui_name, dsl_name):

    global DEPLOYMENT_NAME_MAP
    DEPLOYMENT_NAME_MAP[ui_name] = dsl_name
