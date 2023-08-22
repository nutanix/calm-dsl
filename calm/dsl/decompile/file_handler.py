import os

LOCAL_DIR = None
SCRIPTS_DIR = None
SPECS_DIR = None
BP_DIR = None

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


def init_bp_dir(bp_dir):

    global LOCAL_DIR, SCRIPTS_DIR, SPECS_DIR, BP_DIR
    BP_DIR, LOCAL_DIR, SPECS_DIR, SCRIPTS_DIR = make_bp_dirs(bp_dir)

    return (BP_DIR, LOCAL_DIR, SPECS_DIR, SCRIPTS_DIR)


def init_runbook_dir(runbook_dir):

    global LOCAL_DIR, SCRIPTS_DIR, RUNBOOK_DIR
    RUNBOOK_DIR, LOCAL_DIR, SCRIPTS_DIR = make_runbook_dirs(runbook_dir)

    return (RUNBOOK_DIR, LOCAL_DIR, SCRIPTS_DIR)


def get_bp_dir():
    return BP_DIR


def get_runbook_dir():
    return RUNBOOK_DIR


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
    global LOCAL_DIR, SPECS_DIR, SCRIPTS_DIR, BP_DIR
    LOCAL_DIR = None
    SCRIPTS_DIR = None
    SPECS_DIR = None
    BP_DIR = None
