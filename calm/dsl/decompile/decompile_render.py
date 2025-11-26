import os
from black import format_str, FileMode

from calm.dsl.log import get_logging_handle
from calm.dsl.decompile.bp_file_helper import render_bp_file_template
from calm.dsl.decompile.runbook import render_runbook_template
from calm.dsl.decompile.cloud_provider_file_helper import (
    render_cloud_provider_file_template,
)
from calm.dsl.decompile.file_handler import (
    init_bp_dir,
    init_provider_dir,
    init_runbook_dir,
    init_environment_dir,
    init_project_dir,
    init_global_variable_dir,
)
from calm.dsl.decompile.environments import render_environment_template
from calm.dsl.decompile.projects import render_project_template
from calm.dsl.decompile.global_variable import render_global_variable_template

LOG = get_logging_handle(__name__)


def create_bp_file(dir_name, bp_data):

    bp_path = os.path.join(dir_name, "blueprint.py")
    with open(bp_path, "w") as fd:
        fd.write(bp_data)


def create_provider_file(dir_name, provider_data):

    provider_path = os.path.join(dir_name, "provider.py")
    with open(provider_path, "w") as fd:
        fd.write(provider_data)


def create_runbook_file(dir_name, runbook_data):

    runbook_path = os.path.join(dir_name, "runbook.py")
    with open(runbook_path, "w") as fd:
        fd.write(runbook_data)


def create_project_file(dir_name, project_data):

    project_path = os.path.join(dir_name, "project.py")
    with open(project_path, "w") as fd:
        fd.write(project_data)


def create_environment_file(dir_name, environment_data):

    environment_path = os.path.join(dir_name, "environment.py")
    with open(environment_path, "w") as fd:
        fd.write(environment_data)


def create_global_variable_file(dir_name, global_variable_data):

    gv_path = os.path.join(dir_name, "global_variable.py")
    with open(gv_path, "w") as fd:
        fd.write(global_variable_data)


def create_bp_dir(
    bp_cls=None,
    bp_dir=None,
    with_secrets=False,
    metadata_obj=None,
    contains_encrypted_secrets=False,
    no_format=False,
    global_variable_list=None,
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
        global_variable_list=global_variable_list,
    )

    if not no_format:
        LOG.info("Formatting blueprint file using black")
        bp_data = format_str(bp_data, mode=FileMode())

    LOG.info("Creating blueprint file")
    create_bp_file(bp_dir, bp_data)


def create_provider_dir(
    provider_cls=None,
    provider_dir=None,
    with_secrets=False,
    contains_encrypted_secrets=False,
    no_format=False,
):

    if not provider_dir:
        provider_dir = os.path.join(os.getcwd(), provider_cls.__name__)

    LOG.info("Creating provider directory")
    _, _, _ = init_provider_dir(provider_dir)
    LOG.info("Rendering provider file template")
    provider_data = render_cloud_provider_file_template(
        cls=provider_cls,
        with_secrets=with_secrets,
        contains_encrypted_secrets=contains_encrypted_secrets,
    )

    if not no_format:
        LOG.info("Formatting provider file using black")
        provider_data = format_str(provider_data, mode=FileMode())

    LOG.info("Creating provider file")
    create_provider_file(provider_dir, provider_data)


def create_runbook_dir(
    runbook_cls=None,
    runbook_dir=None,
    metadata_obj=None,
    credentials=None,
    default_endpoint=None,
    global_variable_list=None,
    execution_name=None,
    no_format=False,
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
        global_variable_list=global_variable_list,
        execution_name=execution_name,
    )

    if not no_format:
        LOG.info("Formatting runbook file using black")
        runbook_data = format_str(runbook_data, mode=FileMode())

    LOG.info("Creating runbook file")
    create_runbook_file(runbook_dir, runbook_data)


def create_project_dir(
    project_cls=None, project_dir=None, credentials=None, no_format=False
):
    if not project_dir:
        project_dir = os.path.join(os.getcwd(), project_cls.__name__)

    LOG.info("Creating project directory")
    _, _, _, _ = init_project_dir(project_dir)
    LOG.info("Rendering project file template")
    project_data = render_project_template(
        project_cls=project_cls,
        credentials=credentials,
    )

    if not no_format:
        LOG.info("Formatting project file using black")
        project_data = format_str(project_data, mode=FileMode())

    LOG.info("Creating project file")
    create_project_file(project_dir, project_data)


def create_environment_dir(
    environment_cls=None,
    environment_dir=None,
    metadata_obj=None,
    credentials=None,
    no_format=False,
):
    if not environment_dir:
        environment_dir = os.path.join(os.getcwd(), environment_cls.__name__)

    LOG.info("Creating environment directory")
    _, _, _, _ = init_environment_dir(environment_dir)
    LOG.info("Rendering environment file template")
    environment_data = render_environment_template(
        environment_cls=environment_cls,
        credentials=credentials,
        metadata_obj=metadata_obj,
    )

    if not no_format:
        LOG.info("Formatting environment file using black")
        environment_data = format_str(environment_data, mode=FileMode())

    LOG.info("Creating environment file")
    create_environment_file(environment_dir, environment_data)


def create_global_variable_dir(
    global_variable_cls=None,
    global_variable_dir=None,
    metadata_obj=None,
    no_format=False,
):

    if not global_variable_dir:
        global_variable_dir = os.path.join(os.getcwd(), global_variable_cls.__name__)

    LOG.info("Creating global variable directory")
    _, _, _ = init_global_variable_dir(global_variable_dir)
    LOG.info("Rendering global variable file template")
    global_variable_data = render_global_variable_template(
        global_variable_cls=global_variable_cls, metadata_obj=metadata_obj
    )

    if not no_format:
        LOG.info("Formatting global variable file using black")
        global_variable_data = format_str(global_variable_data, mode=FileMode())

    LOG.info("Creating global variable file")
    create_global_variable_file(global_variable_dir, global_variable_data)
