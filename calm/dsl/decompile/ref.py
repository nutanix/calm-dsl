from calm.dsl.decompile.render import render_template
from calm.dsl.builtins import RefType, ref, Service


def render_ref_template(cls):

    if not isinstance(cls, RefType):
        raise TypeError("{} is not of type {}".format(cls, RefType))

    user_attrs = cls.get_user_attrs()
    schema_file = "ref.py.jinja2"

    text = render_template(schema_file=schema_file, obj=user_attrs)
    return text.strip()


class SampleService(Service):
    pass


ref_cls = ref(SampleService)
print(render_ref_template(ref_cls))
