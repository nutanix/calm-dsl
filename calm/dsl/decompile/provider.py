from calm.dsl.decompile.render import render_template
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def render_provider_template(cls):
    LOG.debug("Rendering {} provider template".format(cls.type))

    if cls.type == "nutanix_pc":
        schema_file = "provider_ntnx.py.jinja2"
    elif cls.type == "aws":
        schema_file = "provider_aws.py.jinja2"
    elif cls.type == "gcp":
        schema_file = "provider_gcp.py.jinja2"
    elif cls.type == "vmware":
        schema_file = "provider_vmware.py.jinja2"

    user_attrs = cls.get_user_attrs()
    text = render_template(schema_file=schema_file, obj=user_attrs)
    return text.strip()
