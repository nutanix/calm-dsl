from jinja2 import Environment, PackageLoader


def get_template():

    loader = PackageLoader(__name__, "schemas")
    env = Environment(loader=loader)
    template = env.get_template("main.py.jinja2")
    return template


def render_template(macro_name, obj):

    template = get_template()
    text=template.render(macro_name=macro_name, obj=obj)

    return text.strip()
