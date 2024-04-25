from calm.dsl.decompile.render import render_template
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def render_user_template(cls):
    LOG.debug("Rendering {} user template".format(cls["name"]))

    schema_file = "user.py.jinja2"
    user_attrs = {"name": cls["name"]}
    text = render_template(schema_file=schema_file, obj=user_attrs)
    return text.strip()
