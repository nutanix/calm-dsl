from calm.dsl.decompile.render import render_template
from calm.dsl.builtins import RefType
from calm.dsl.tools import get_logging_handle

LOG = get_logging_handle(__name__)


def render_ref_template(cls):

    LOG.debug("Rendering {} ref template".format(cls.__name__))
    if not isinstance(cls, RefType):
        raise TypeError("{} is not of type {}".format(cls, RefType))

    user_attrs = cls.get_user_attrs()
    user_attrs["name"] = cls.__name__
    schema_file = "ref.py.jinja2"

    text = render_template(schema_file=schema_file, obj=user_attrs)
    return text.strip()
