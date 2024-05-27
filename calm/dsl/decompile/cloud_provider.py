from calm.dsl.builtins.models.cloud_provider import CloudProviderType

# from calm.dsl.constants import CLOUD_PROVIDER as PROVIDER
from calm.dsl.decompile.action import render_action_template
from calm.dsl.decompile.ndb import modify_var_format
from calm.dsl.decompile.render import render_template
from calm.dsl.decompile.credential import get_cred_var_name
from calm.dsl.decompile.variable import render_variable_template
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def render_cloud_provider_template(cls, secrets_dict):

    LOG.debug("Rendering {} provider template".format(cls.__name__))
    if not isinstance(cls, CloudProviderType):
        raise TypeError("{} is not of type {}".format(cls, CloudProviderType))

    user_attrs = cls.get_user_attrs()
    user_attrs["name"] = cls.__name__
    user_attrs["description"] = cls.__doc__ or ""

    entity_context = "CloudProvider_" + cls.__name__
    auth_schema_variables = []
    for entity in user_attrs.get("auth_schema_variables", []):
        var_template = render_variable_template(
            entity,
            entity_context,
            secrets_dict=secrets_dict,
            variable_context="auth_schema",
        )
        auth_schema_variables.append(modify_var_format(var_template))

    provider_variables = []
    for entity in user_attrs.get("variables", []):
        var_template = render_variable_template(
            entity,
            entity_context,
            secrets_dict=secrets_dict,
        )
        provider_variables.append(modify_var_format(var_template))

    endpoint_schema_variables = []
    endpoint_schema = user_attrs.get("endpoint_schema")
    if endpoint_schema:
        for entity in endpoint_schema.variables:
            var_template = render_variable_template(
                entity,
                entity_context,
                secrets_dict=secrets_dict,
                variable_context="endpoint_schema",
            )
            endpoint_schema_variables.append(modify_var_format(var_template))

    test_account_variables = []
    test_account = user_attrs.get("test_account")
    if test_account:
        for entity in test_account.variables:
            var_template = render_variable_template(
                entity,
                entity_context,
                secrets_dict=secrets_dict,
                variable_context="test_account_variable",
            )
            test_account_variables.append(modify_var_format(var_template))

    credential_list = []
    for cred in cls.credentials:
        credential_list.append(
            get_cred_var_name(getattr(cred, "name", "") or cred.__name__)
        )

    resource_types = []
    for resource_type in cls.resource_types:
        resource_types.append(resource_type.__name__)

    action_list = []
    for action in user_attrs.get("actions", []):
        action_list.append(
            render_action_template(
                action, entity_context=entity_context, secrets_dict=secrets_dict
            )
        )

    user_attrs.update(
        {
            "auth_schema_variables": auth_schema_variables,
            "variables": provider_variables,
            "endpoint_schema_variables": endpoint_schema_variables,
            "test_account_variables": test_account_variables,
            "resource_types": ", ".join(resource_types),
            "credentials": ", ".join(credential_list),
            "actions": action_list,
        }
    )

    text = render_template("cloud_provider.py.jinja2", obj=user_attrs)
    return text.strip()
