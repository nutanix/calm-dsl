import os
import sys
from jinja2 import Environment, PackageLoader
from Crypto.PublicKey import RSA

from calm.dsl.config import get_config
from calm.dsl.api import get_api_client
from calm.dsl.store import Cache
from calm.dsl.builtins import read_file
from calm.dsl.tools import get_logging_handle

LOG = get_logging_handle(__name__)


def render_ahv_template(template, bp_name):

    # Getting the subnet registered to the project
    client = get_api_client()
    config = get_config()

    project_name = config["PROJECT"].get("name", "default")
    project_cache_data = Cache.get_entity_data(entity_type="project", name=project_name)
    if not project_cache_data:
        LOG.error(
            "Project {} not found. Please run: calm update cache".format(project_name)
        )
        sys.exit(-1)
    project_uuid = project_cache_data.get("uuid", "")

    LOG.info("Fetching ahv subnets attached to the project {}".format(project_name))
    res, err = client.project.read(project_uuid)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    res = res.json()
    subnets = res["status"]["project_status"]["resources"].get(
        "subnet_reference_list", []
    )

    # Fetching external subnets
    external_networks = res["status"]["project_status"]["resources"].get(
        "external_network_list", []
    )
    subnets.extend(external_networks)

    if not subnets:
        raise Exception("no subnets registered !!!")

    default_subnet = subnets[0]["name"]
    subnet_cache_data = Cache.get_entity_data(
        entity_type="ahv_subnet", name=default_subnet
    )
    if not subnet_cache_data:
        LOG.error(
            "Subnet {} not found. Please run: calm update cache".format(default_subnet)
        )
        sys.exit(-1)
    cluster_name = subnet_cache_data.get("cluster", "")

    LOG.info("Rendering ahv template")
    text = template.render(
        bp_name=bp_name, subnet_name=default_subnet, cluster_name=cluster_name
    )

    return text.strip() + os.linesep


template_map = {
    "AHV_VM": ("ahv_blueprint.py.jinja2", render_ahv_template),
}


def render_blueprint_template(bp_name, provider_type):

    if provider_type not in template_map:
        print(
            "Provider {} not supported. Using AHV_VM as provider".format(provider_type)
        )
        provider_type = "AHV_VM"

    schema_file, temp_render_helper = template_map.get(provider_type)

    loader = PackageLoader(__name__, "")
    env = Environment(loader=loader)
    template = env.get_template(schema_file)

    return temp_render_helper(template, bp_name)


def create_bp_file(dir_name, bp_name, provider_type):

    bp_text = render_blueprint_template(bp_name, provider_type)
    bp_path = os.path.join(dir_name, "blueprint.py")

    LOG.info("Writing bp file to {}".format(bp_path))
    with open(bp_path, "w") as fd:
        fd.write(bp_text)


def create_cred_keys(dir_name):

    # Will create key via name centos/centos_pub

    key = RSA.generate(2048)

    # Write private key
    private_key = key.export_key("PEM")
    private_key_filename = os.path.join(dir_name, "centos")
    with open(private_key_filename, "wb") as fd:
        fd.write(private_key)
    os.chmod(private_key_filename, 0o600)

    # Write public key
    public_key = key.publickey().export_key("OpenSSH")
    public_key_filename = os.path.join(dir_name, "centos_pub")
    with open(public_key_filename, "wb") as fd:
        fd.write(public_key)
    os.chmod(public_key_filename, 0o600)


def create_scripts(dir_name):

    dir_path = os.path.dirname(os.path.realpath(__file__))
    scripts_dir = os.path.join(dir_path, "scripts")
    for script_file in os.listdir(scripts_dir):
        script_path = os.path.join(scripts_dir, script_file)
        data = read_file(script_path)

        with open(os.path.join(dir_name, script_file), "w+") as fd:
            fd.write(data)


def make_bp_dirs(dir_name, bp_name):

    bp_dir = "{}Blueprint".format(os.path.join(dir_name, bp_name))
    if not os.path.isdir(bp_dir):
        os.makedirs(bp_dir)

    local_dir = os.path.join(bp_dir, ".local")
    if not os.path.isdir(local_dir):
        os.makedirs(local_dir)

    key_dir = os.path.join(local_dir, "keys")
    if not os.path.isdir(key_dir):
        os.makedirs(key_dir)

    script_dir = os.path.join(bp_dir, "scripts")
    if not os.path.isdir(script_dir):
        os.makedirs(script_dir)

    return (bp_dir, key_dir, script_dir)


def init_bp(bp_name, dir_name, provider_type):

    bp_name = bp_name.strip().split()[0].title()
    bp_dir, key_dir, script_dir = make_bp_dirs(dir_name, bp_name)

    # sync cache
    Cache.sync()

    # Creating keys
    LOG.info("Generating keys for credentials")
    create_cred_keys(key_dir)

    # create scripts
    create_scripts(script_dir)

    create_bp_file(bp_dir, bp_name, provider_type)
