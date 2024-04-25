from calm.dsl.decompile.render import render_template
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def render_quotas_template(cls):
    LOG.debug("Rendering quotas template")

    schema_file = "quotas.py.jinja2"
    user_attrs = {
        "vcpus": cls["vcpus"],
        "storage": cls["storage"],
        "memory": cls["memory"],
    }
    text = render_template(schema_file=schema_file, obj=user_attrs)
    return text.strip()
