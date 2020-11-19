import os
from jinja2 import Environment, PackageLoader

from calm.dsl.builtins import read_file
from calm.dsl.log import get_logging_handle
from calm.dsl.config import get_context

LOG = get_logging_handle(__name__)


def render_runbook_template(runbook_name):

    schema_file = "runbook.py.jinja2"

    loader = PackageLoader(__name__, "")
    env = Environment(loader=loader)
    template = env.get_template(schema_file)
    LOG.info("Rendering runbook template")

    ContextObj = get_context()
    server_config = ContextObj.get_server_config()
    pc_ip = server_config["pc_ip"]
    pc_port = server_config["pc_port"]
    text = template.render(
        runbook_name=runbook_name,
        pc_ip=pc_ip,
        pc_port=pc_port,
    )
    LOG.info("Success")

    return text.strip() + os.linesep


def create_runbook_file(dir_name, runbook_name):

    rb_text = render_runbook_template(runbook_name)
    rb_path = os.path.join(dir_name, "runbook.py")

    LOG.info("Writing runbook file to {}".format(rb_path))
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


def make_runbook_dirs(dir_name, runbook_name):

    runbook_dir = "{}Runbook".format(os.path.join(dir_name, runbook_name))
    if not os.path.isdir(runbook_dir):
        os.makedirs(runbook_dir)

    script_dir = os.path.join(runbook_dir, "scripts")
    if not os.path.isdir(script_dir):
        os.makedirs(script_dir)

    return (runbook_dir, script_dir)


def init_runbook(runbook_name, dir_name):

    runbook_name = runbook_name.strip().split()[0].title()
    runbook_dir, script_dir = make_runbook_dirs(dir_name, runbook_name)

    # create scripts
    create_scripts(script_dir)

    create_runbook_file(runbook_dir, runbook_name)
