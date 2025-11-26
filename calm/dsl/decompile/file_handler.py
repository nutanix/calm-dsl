import os

LOCAL_DIR = None
SCRIPTS_DIR = None
SPECS_DIR = None
BP_DIR = None
PROVIDER_DIR = None
GLOBAL_VARIABLE_DIR = None

LOCAL_DIR_KEY = ".local"
SCRIPTS_DIR_KEY = "scripts"
SPECS_DIR_KEY = "specs"


def make_bp_dirs(bp_dir):

    if not os.path.isdir(bp_dir):
        os.makedirs(bp_dir)

    local_dir = os.path.join(bp_dir, LOCAL_DIR_KEY)
    if not os.path.isdir(local_dir):
        os.makedirs(local_dir)

    spec_dir = os.path.join(bp_dir, SPECS_DIR_KEY)
    if not os.path.isdir(spec_dir):
        os.makedirs(spec_dir)

    scripts_dir = os.path.join(bp_dir, SCRIPTS_DIR_KEY)
    if not os.path.isdir(scripts_dir):
        os.makedirs(scripts_dir)

    return (bp_dir, local_dir, spec_dir, scripts_dir)


def make_provider_dirs(provider_dir):

    if not os.path.isdir(provider_dir):
        os.makedirs(provider_dir)

    local_dir = os.path.join(provider_dir, LOCAL_DIR_KEY)
    if not os.path.isdir(local_dir):
        os.makedirs(local_dir)

    scripts_dir = os.path.join(provider_dir, SCRIPTS_DIR_KEY)
    if not os.path.isdir(scripts_dir):
        os.makedirs(scripts_dir)

    return (provider_dir, local_dir, scripts_dir)


def make_runbook_dirs(runbook_dir):

    if not os.path.isdir(runbook_dir):
        os.makedirs(runbook_dir)

    local_dir = os.path.join(runbook_dir, LOCAL_DIR_KEY)
    if not os.path.isdir(local_dir):
        os.makedirs(local_dir)

    scripts_dir = os.path.join(runbook_dir, SCRIPTS_DIR_KEY)
    if not os.path.isdir(scripts_dir):
        os.makedirs(scripts_dir)

    return (runbook_dir, local_dir, scripts_dir)


def make_project_dirs(project_dir):

    if not os.path.isdir(project_dir):
        os.makedirs(project_dir)

    local_dir = os.path.join(project_dir, LOCAL_DIR_KEY)
    if not os.path.isdir(local_dir):
        os.makedirs(local_dir)

    spec_dir = os.path.join(project_dir, SPECS_DIR_KEY)
    if not os.path.isdir(spec_dir):
        os.makedirs(spec_dir)

    scripts_dir = os.path.join(project_dir, SCRIPTS_DIR_KEY)
    if not os.path.isdir(scripts_dir):
        os.makedirs(scripts_dir)

    return (project_dir, local_dir, spec_dir, scripts_dir)


def make_environment_dirs(environment_dir):

    if not os.path.isdir(environment_dir):
        os.makedirs(environment_dir)

    local_dir = os.path.join(environment_dir, LOCAL_DIR_KEY)
    if not os.path.isdir(local_dir):
        os.makedirs(local_dir)

    spec_dir = os.path.join(environment_dir, SPECS_DIR_KEY)
    if not os.path.isdir(spec_dir):
        os.makedirs(spec_dir)

    scripts_dir = os.path.join(environment_dir, SCRIPTS_DIR_KEY)
    if not os.path.isdir(scripts_dir):
        os.makedirs(scripts_dir)

    return (environment_dir, local_dir, spec_dir, scripts_dir)


def make_global_variable_dirs(global_variable_dir):

    if not os.path.isdir(global_variable_dir):
        os.makedirs(global_variable_dir)

    local_dir = os.path.join(global_variable_dir, LOCAL_DIR_KEY)
    if not os.path.isdir(local_dir):
        os.makedirs(local_dir)

    scripts_dir = os.path.join(global_variable_dir, SCRIPTS_DIR_KEY)
    if not os.path.isdir(scripts_dir):
        os.makedirs(scripts_dir)

    return (global_variable_dir, local_dir, scripts_dir)


def init_bp_dir(bp_dir):

    global LOCAL_DIR, SCRIPTS_DIR, SPECS_DIR, BP_DIR
    BP_DIR, LOCAL_DIR, SPECS_DIR, SCRIPTS_DIR = make_bp_dirs(bp_dir)

    return (BP_DIR, LOCAL_DIR, SPECS_DIR, SCRIPTS_DIR)


def init_provider_dir(provider_dir):

    global LOCAL_DIR, SCRIPTS_DIR, PROVIDER_DIR
    PROVIDER_DIR, LOCAL_DIR, SCRIPTS_DIR = make_provider_dirs(provider_dir)

    return (PROVIDER_DIR, LOCAL_DIR, SCRIPTS_DIR)


def init_runbook_dir(runbook_dir):

    global LOCAL_DIR, SCRIPTS_DIR, RUNBOOK_DIR
    RUNBOOK_DIR, LOCAL_DIR, SCRIPTS_DIR = make_runbook_dirs(runbook_dir)

    return (RUNBOOK_DIR, LOCAL_DIR, SCRIPTS_DIR)


def init_project_dir(project_dir):

    global LOCAL_DIR, SCRIPTS_DIR, SPECS_DIR, PROJECT_DIR
    PROJECT_DIR, LOCAL_DIR, SPECS_DIR, SCRIPTS_DIR = make_project_dirs(project_dir)

    return (PROJECT_DIR, LOCAL_DIR, SPECS_DIR, SCRIPTS_DIR)


def init_environment_dir(environment_dir):

    global LOCAL_DIR, SCRIPTS_DIR, SPECS_DIR, ENVIRONMENT_DIR
    ENVIRONMENT_DIR, LOCAL_DIR, SPECS_DIR, SCRIPTS_DIR = make_environment_dirs(
        environment_dir
    )

    return (ENVIRONMENT_DIR, LOCAL_DIR, SPECS_DIR, SCRIPTS_DIR)


def init_global_variable_dir(global_variable_dir):

    global LOCAL_DIR, SCRIPTS_DIR, GLOBAL_VARIABLE_DIR
    GLOBAL_VARIABLE_DIR, LOCAL_DIR, SCRIPTS_DIR = make_global_variable_dirs(
        global_variable_dir
    )

    return (GLOBAL_VARIABLE_DIR, LOCAL_DIR, SCRIPTS_DIR)


def get_bp_dir():
    return BP_DIR


def get_global_variable_dir():
    return GLOBAL_VARIABLE_DIR


def get_provider_dir():
    return PROVIDER_DIR


def get_runbook_dir():
    return RUNBOOK_DIR


def get_project_dir():
    return PROJECT_DIR


def get_environment_dir():
    return ENVIRONMENT_DIR


def get_environment_dir():
    return ENVIRONMENT_DIR


def get_local_dir():
    return LOCAL_DIR


def get_specs_dir():
    return SPECS_DIR


def get_scripts_dir():
    return SCRIPTS_DIR


def get_local_dir_key():
    return LOCAL_DIR_KEY


def get_specs_dir_key():
    return SPECS_DIR_KEY


def get_scripts_dir_key():
    return SCRIPTS_DIR_KEY


def init_file_globals():
    global LOCAL_DIR, SPECS_DIR, SCRIPTS_DIR, BP_DIR, PROVIDER_DIR, GLOBAL_VARIABLE_DIR
    LOCAL_DIR = None
    SCRIPTS_DIR = None
    SPECS_DIR = None
    BP_DIR = None
    PROVIDER_DIR = None
    GLOBAL_VARIABLE_DIR = None
