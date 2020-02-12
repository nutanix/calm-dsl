import os
from jinja2 import Environment, PackageLoader
from Crypto.PublicKey import RSA

from calm.dsl.config import get_config
from calm.dsl.api import get_api_client
from calm.dsl.store import Cache
from calm.dsl.builtins import read_file
from calm.dsl.tools import get_logging_handle

LOG = get_logging_handle(__name__)

template_map = {
    "AHV_VM": ("ahv_blueprint.py.jinja2", render_ahv_template),
}

def create_bp_file(dir_name, service_name, provider_type):

    bp_text = render_blueprint_template(service_name, provider_type)
    bp_path = os.path.join(dir_name, "blueprint.py")

    LOG.info("Writing bp file to {}".format(bp_path))
    with open(bp_path, "w") as fd:
        fd.write(bp_text)
    LOG.info("Success")

def create_scripts(dir_name):

    dir_path = os.path.dirname(os.path.realpath(__file__))
    scripts_dir = os.path.join(dir_path, "scripts")
    for script_file in os.listdir(scripts_dir):
        script_path = os.path.join(scripts_dir, script_file)
        data = read_file(script_path)

        with open(os.path.join(dir_name, script_file), "w+") as fd:
            fd.write(data)


def make_bp_dirs(dir_name, bp_name):

    bp_dir = os.path.join(dir_name, bp_name)
    if not os.path.isdir(bp_dir):
        os.makedirs(bp_dir)

    local_dir = os.path.join(bp_dir, ".local")
    if not os.path.isdir(local_dir):
        os.makedirs(local_dir)

    spec_dir = os.path.join(bp_dir, "spec")
    if not os.path.isdir(spec_dir):
        os.makedirs(spec_dir)

    return (bp_dir, local_dir, spec_dir)


def dsl_bp(service_name, dir_name, provider_type):

    bp_name = "{}Blueprint".format(service_name,)

    bp_dir, local_dir, spec_dir = make_bp_dirs(dir_name, bp_name)

    create_bp_file(bp_dir, service_name, provider_type)


def main():
    service_name = "Hello"
    dir_name = os.getcwd()
    dsl_bp(service_name, dir_name)

