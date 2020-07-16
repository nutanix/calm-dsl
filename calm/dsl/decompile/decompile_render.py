import os
from black import format_str, FileMode

from calm.dsl.log import get_logging_handle
from calm.dsl.decompile.bp_file_helper import render_bp_file_template
from calm.dsl.decompile.file_handler import init_bp_dir

LOG = get_logging_handle(__name__)


def create_bp_file(dir_name, bp_data):

    bp_path = os.path.join(dir_name, "blueprint.py")
    with open(bp_path, "w") as fd:
        fd.write(bp_data)


def create_bp_dir(bp_cls=None, bp_dir_name=None, with_secrets=False):

    bp_dir_name = bp_dir_name or bp_cls.__name__
    dir_name = os.getcwd()

    LOG.info("Creating blueprint directory")
    bp_dir, _, _, _ = init_bp_dir(dir_name, bp_dir_name)
    LOG.info("Rendering blueprint file template")
    bp_data = render_bp_file_template(bp_cls, with_secrets)
    LOG.info("Formatting blueprint file using black")
    bp_data = format_str(bp_data, mode=FileMode())
    LOG.info("Creating blueprint file")
    create_bp_file(bp_dir, bp_data)
