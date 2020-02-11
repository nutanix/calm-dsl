from jinja2 import Environment, PackageLoader


def get_template(schema_file):

    loader = PackageLoader(__name__, "schemas")
    env = Environment(loader=loader)
    template = env.get_template(schema_file)
    return template


def render_template(schema_file, obj):

    template = get_template(schema_file)
    text = template.render(obj=obj)

    return text.strip()
