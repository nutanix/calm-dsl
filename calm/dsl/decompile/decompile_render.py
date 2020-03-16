import os
from black import format_str, FileMode

from calm.dsl.decompile.bp_file_helper import render_bp_file_template
from calm.dsl.decompile.file_handler import init_bp_dir


def create_bp_file(dir_name, bp_data):

    bp_path = os.path.join(dir_name, "blueprint.py")
    with open(bp_path, "w") as fd:
        fd.write(bp_data)


def create_bp_dir(bp_cls=None):

    bp_name = bp_cls.__name__ or "SampleBlueprint"
    dir_name = os.getcwd()

    bp_dir, local_dir, spec_dir, scripts_dir = init_bp_dir(dir_name, bp_name)
    bp_data = render_bp_file_template(bp_cls, local_dir, spec_dir)
    bp_data = format_str(bp_data, mode=FileMode())

    create_bp_file(bp_dir, bp_data)
