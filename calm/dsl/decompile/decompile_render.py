import os
from black import format_str, FileMode

from calm.dsl.builtins import read_file
from tests.decompile.test_decompile import bp_cls as NextBlueprint
from calm.dsl.decompile.bp_file_helper import render_bp_file_template



def create_bp_file(dir_name, bp_data):

    bp_path = os.path.join(dir_name, "blueprint.py")
    with open(bp_path, "w") as fd:
        fd.write(bp_data)

def create_scripts(dir_name):

    dir_path = os.path.dirname(os.path.realpath(__file__))
    scripts_dir = os.path.join(dir_path, "scripts")
    for script_file in os.listdir(scripts_dir):
        script_path = os.path.join(scripts_dir, script_file)
        data = read_file(script_path)

        with open(os.path.join(dir_name, script_file), "w+") as fd:
            fd.write(data)

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

    return (bp_dir, local_dir, spec_dir)


def create_bp_dir(bp_cls = None):

    bp_name = bp_cls.__name__ or "SampleBlueprint"
    dir_name = os.getcwd()

    bp_dir, local_dir, spec_dir = make_bp_dirs(dir_name, bp_name)
    bp_data = render_bp_file_template(bp_cls, local_dir, spec_dir)
    bp_data = format_str(bp_data, mode=FileMode())

    create_bp_file(bp_dir, bp_data)
