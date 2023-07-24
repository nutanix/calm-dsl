from calm.dsl.decompile.render import render_template
from .decompile_helpers import process_variable_name


def render_endpoint(ep):
    name = ep.name
    usr_attrs = {"var_name": process_variable_name(name), "name": name}
    text = render_template(schema_file="endpoint.py.jinja2", obj=usr_attrs)
    return text.strip()
