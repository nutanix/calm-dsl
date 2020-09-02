from calm.dsl.decompile.render import render_template
from calm.dsl.builtins import ReadinessProbeType
from calm.dsl.decompile.credential import get_cred_var_name
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def render_readiness_probe_template(cls):

    LOG.debug("Rendering {} readiness probe template".format(cls.__name__))
    if not isinstance(cls, ReadinessProbeType):
        raise TypeError("{} is not of type {}".format(cls, ReadinessProbeType))

    user_attrs = cls.get_user_attrs()

    # deal with cred
    cred = user_attrs["credential"]
    if cred:
        user_attrs["credential"] = "ref({})".format(get_cred_var_name(cred.__name__))

    schema_file = "readiness_probe.py.jinja2"

    text = render_template(schema_file=schema_file, obj=user_attrs)
    return text.strip()
