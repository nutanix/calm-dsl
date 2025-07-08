from calm.dsl.decompile.render import render_template
from calm.dsl.decompile.ref import render_ref_template
from calm.dsl.decompile.provider import render_provider_template
from calm.dsl.decompile.user import render_user_template
from calm.dsl.decompile.quotas import render_quotas_template
from calm.dsl.builtins.models.project import ProjectType
from .decompile_helpers import process_variable_name
from calm.dsl.builtins import get_valid_identifier
from calm.dsl.store import Cache

from calm.dsl.decompile.credential import (
    render_credential_template,
    get_cred_files,
    get_cred_var_name,
)

from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def render_project_template(
    project_cls,
    entity_context="",
    CONFIG_SPEC_MAP={},
    credentials=[],
):
    LOG.debug("Rendering {} project template".format(project_cls.__name__))
    if not isinstance(project_cls, ProjectType):
        sys.exit("{} is not of type {}".format(project_cls, project))
    # Update entity context
    entity_context = entity_context + "_Project_" + project_cls.__name__

    project_name = getattr(project_cls, "name", "") or project_cls.__name__

    user_attrs = {
        "name": project_cls.__name__,
        "tunnels": [],
    }

    tunnel_refs = project_cls.get_dict().get("tunnel_reference_list", [])
    if tunnel_refs:
        for tunnel in tunnel_refs:
            user_attrs["tunnels"].append(tunnel)

    rendered_providers_list = []
    if project_cls.providers:
        for provider in project_cls.providers:
            rendered_providers_list.append(render_provider_template(provider))
    user_attrs["providers"] = rendered_providers_list

    rendered_users_list = []
    if project_cls.users:
        for user in project_cls.users:
            rendered_users_list.append(render_user_template(user))
    user_attrs["users"] = rendered_users_list

    if project_cls.quotas:
        quotas = render_quotas_template(project_cls.quotas)
        user_attrs["quotas"] = quotas

    gui_display_name = getattr(project_cls, "name", "") or project_cls.__name__
    if gui_display_name != project_cls.__name__:
        user_attrs["gui_display_name"] = gui_display_name

    text = render_template(schema_file="projects.py.jinja2", obj=user_attrs)
    return text.strip()
