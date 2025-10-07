import sys

from calm.dsl.decompile.render import render_template
from calm.dsl.decompile.variable import (
    render_variable_template,
    get_secret_variable_files,
)
from calm.dsl.decompile.endpoint import render_endpoint

from calm.dsl.builtins import CalmEndpoint as Endpoint
from calm.dsl.builtins.models.global_variable import GlobalVariableType
from calm.dsl.log import get_logging_handle
from calm.dsl.store import Cache
from calm.dsl.constants import CACHE

LOG = get_logging_handle(__name__)


def render_global_variable_template(
    global_variable_cls,
    metadata_obj=None,
    entity_context="",
):
    LOG.debug(
        "Rendering {} global variable template".format(global_variable_cls.__name__)
    )
    if not isinstance(global_variable_cls, GlobalVariableType):
        LOG.error("{} is not of type GlobalVariableType".format(global_variable_cls))
        sys.exit("{} is not of type GlobalVariableType".format(global_variable_cls))

    entity_context = entity_context + "_GlobalVariable_" + global_variable_cls.__name__
    global_variable_name = (
        getattr(global_variable_cls, "name", "") or global_variable_cls.__name__
    )

    endpoints = []
    var_definition = global_variable_cls.definition
    setattr(var_definition, "__name__", "definition")
    calmvar = render_variable_template(
        var_definition, entity_context, endpoints=endpoints, is_global_variable=True
    )
    secret_files = get_secret_variable_files()

    project_name = metadata_obj.project.get("name", "")

    projects = []
    for uuid in global_variable_cls.projects:
        project_cache_data = Cache.get_entity_data_using_uuid(
            entity_type=CACHE.ENTITY.PROJECT, uuid=uuid
        )
        if not project_cache_data:
            LOG.error(
                "Project with uuid: {} not found. Please run: calm update cache".format(
                    uuid
                )
            )
            sys.exit(
                "Project with uuid: {} not found. Please run: calm update cache".format(
                    uuid
                )
            )
        projects.append(project_cache_data["name"])

    user_attrs = {
        "name": global_variable_name,
        "variable": calmvar,
        "projects": projects,
        "project_name": project_name,
        "endpoints": endpoints,
        "secret_files": secret_files,
    }

    text = render_template(schema_file="global_variable.py.jinja2", obj=user_attrs)
    return text.strip()
