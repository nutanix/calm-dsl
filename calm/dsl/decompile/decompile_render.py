import os
from black import format_str, FileMode

from calm.dsl.log import get_logging_handle
from calm.dsl.decompile.bp_file_helper import render_bp_file_template
from calm.dsl.decompile.runbook import render_runbook_template
from calm.dsl.decompile.file_handler import init_bp_dir, init_runbook_dir

LOG = get_logging_handle(__name__)


def create_bp_file(dir_name, bp_data):

    bp_path = os.path.join(dir_name, "blueprint.py")
    with open(bp_path, "w") as fd:
        fd.write(bp_data)


def create_runbook_file(dir_name, runbook_data):

    runbook_path = os.path.join(dir_name, "runbook.py")
    with open(runbook_path, "w") as fd:
        fd.write(runbook_data)


def create_bp_dir(
    bp_cls=None,
    bp_dir=None,
    with_secrets=False,
    metadata_obj=None,
    contains_encrypted_secrets=False,
):

    if not bp_dir:
        bp_dir = os.path.join(os.getcwd(), bp_cls.__name__)

    LOG.info("Creating blueprint directory")
    _, _, _, _ = init_bp_dir(bp_dir)
    LOG.info("Rendering blueprint file template")
    bp_data = render_bp_file_template(
        cls=bp_cls,
        with_secrets=with_secrets,
        metadata_obj=metadata_obj,
        contains_encrypted_secrets=contains_encrypted_secrets,
    )
    LOG.info("Formatting blueprint file using black")
    bp_data = format_str(bp_data, mode=FileMode())
    LOG.info("Creating blueprint file")
    create_bp_file(bp_dir, bp_data)


def create_runbook_dir(
    runbook_cls=None,
    runbook_dir=None,
    metadata_obj=None,
    credentials=None,
    default_endpoint=None,
):
    if not runbook_dir:
        runbook_dir = os.path.join(os.getcwd(), runbook_cls.__name__)

    LOG.info("Creating runbook directory")
    _, _, _ = init_runbook_dir(runbook_dir)
    LOG.info("Rendering runbook file template")
    runbook_data = render_runbook_template(
        runbook_cls=runbook_cls,
        credentials=credentials,
        metadata_obj=metadata_obj,
        default_endpoint=default_endpoint,
    )

    LOG.info("Formatting runbook file using black")
    runbook_data = format_str(runbook_data, mode=FileMode())
    LOG.info("Creating runbook file")
    create_runbook_file(runbook_dir, runbook_data)
