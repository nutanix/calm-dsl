import os

LOCAL_DIR = None
SCRIPTS_DIR = None
SPECS_DIR = None
BP_DIR = None


def make_bp_dirs(dir_name, bp_name):

    bp_dir = os.path.join(dir_name, bp_name)
    if not os.path.isdir(bp_dir):
        os.makedirs(bp_dir)

    local_dir = os.path.join(bp_dir, ".local")
    if not os.path.isdir(local_dir):
        os.makedirs(local_dir)

    spec_dir = os.path.join(bp_dir, "specs")
    if not os.path.isdir(spec_dir):
        os.makedirs(spec_dir)

    scripts_dir = os.path.join(bp_dir, "scripts")
    if not os.path.isdir(scripts_dir):
        os.makedirs(scripts_dir)

    return (bp_dir, local_dir, spec_dir, scripts_dir)


def init_bp_dir(dir_name, bp_name):

    global LOCAL_DIR, SCRIPTS_DIR, SPECS_DIR, BP_DIR
    BP_DIR, LOCAL_DIR, SPECS_DIR, SCRIPTS_DIR = make_bp_dirs(dir_name, bp_name)

    return (BP_DIR, LOCAL_DIR, SPECS_DIR, SCRIPTS_DIR)


def get_bp_dir():
    return BP_DIR


def get_local_dir():
    return LOCAL_DIR


def get_specs_dir():
    return SPECS_DIR


def get_scripts_dir():
    return SCRIPTS_DIR
