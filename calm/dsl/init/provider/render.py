import os
from jinja2 import Environment, PackageLoader

from calm.dsl.builtins import read_file
from calm.dsl.log import get_logging_handle
from calm.dsl.config import get_context

LOG = get_logging_handle(__name__)


def render_provider_template(provider_name):

    schema_file = "provider.py.jinja2"

    loader = PackageLoader(__name__, "")
    env = Environment(loader=loader)
    template = env.get_template(schema_file)
    LOG.info("Rendering provider template")

    ContextObj = get_context()
    server_config = ContextObj.get_server_config()
    pc_ip = server_config["pc_ip"]
    pc_port = server_config["pc_port"]
    text = template.render(
        provider_name=provider_name,
        pc_ip=pc_ip,
        pc_port=pc_port,
    )
    LOG.info("Success")

    return text.strip() + os.linesep


def create_provider_file(dir_name, provider_name):

    rb_text = render_provider_template(provider_name)
    rb_path = os.path.join(dir_name, "provider.py")

    LOG.info("Writing provider file to {}".format(rb_path))
    with open(rb_path, "w") as fd:
        fd.write(rb_text)
    LOG.info("Success")


def create_scripts(dir_name):

    dir_path = os.path.dirname(os.path.realpath(__file__))
    scripts_dir = os.path.join(dir_path, "scripts")
    for script_file in os.listdir(scripts_dir):
        script_path = os.path.join(scripts_dir, script_file)
        data = read_file(script_path)

        with open(os.path.join(dir_name, script_file), "w+") as fd:
            fd.write(data)


def make_provider_dirs(dir_name, provider_name):

    provider_dir = "{}Provider".format(os.path.join(dir_name, provider_name))
    if not os.path.isdir(provider_dir):
        os.makedirs(provider_dir)

    script_dir = os.path.join(provider_dir, "scripts")
    if not os.path.isdir(script_dir):
        os.makedirs(script_dir)

    return (provider_dir, script_dir)


def init_provider(provider_name, dir_name):

    provider_name = provider_name.strip().split()[0].title()
    provider_dir, script_dir = make_provider_dirs(dir_name, provider_name)

    create_scripts(script_dir)

    create_provider_file(provider_dir, provider_name)
