import os
from jinja2 import Environment, PackageLoader
from Crypto.PublicKey import RSA

from calm.dsl.config import get_config
from calm.dsl.api import get_api_client
from calm.dsl.store import Cache
from calm.dsl.builtins import read_file


template_map = {
    "AHV_VM": "ahv_blueprint.py.jinja2",
}


def render_blueprint_template(service_name, subnet_name, provider_type):

    service_name = service_name.strip().split()[0].title()

    if provider_type not in template_map:
        print(
            "Provider {} not supported. Using AHV_VM as provider ...".format(
                provider_type
            )
        )
        provider_type = "AHV_VM"

    schema_file = template_map.get(provider_type)

    loader = PackageLoader(__name__, "")
    env = Environment(loader=loader)
    template = env.get_template(schema_file)
    text = template.render(service_name=service_name, subnet_name=subnet_name)
    return text.strip() + "\n"


def create_bp_file(dir_name, service_name, subnet_name, provider_type):

    bp_text = render_blueprint_template(service_name, subnet_name, provider_type)

    bp_path = os.path.join(dir_name, "blueprint.py")

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

    bp_dir = os.path.join(dir_name, bp_name)
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

    return (bp_dir, local_dir, key_dir, script_dir)


def init_bp(service_name, dir_name, provider_type):

    bp_name = "{}Blueprint".format(service_name,)

    bp_dir, local_dir, key_dir, script_dir = make_bp_dirs(dir_name, bp_name)

    # sync cache
    Cache.sync()

    # Getting the subnet registered to the project
    client = get_api_client()
    config = get_config()

    project_name = config["PROJECT"].get("name", "default")
    project_uuid = Cache.get_entity_uuid("PROJECT", project_name)

    res, err = client.project.read(project_uuid)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    res = res.json()

    subnets = res["status"]["project_status"]["resources"].get(
        "subnet_reference_list", []
    )
    if not subnets:
        raise Exception("no subnets registered !!!")

    default_subnet = subnets[0]["name"]

    create_bp_file(bp_dir, service_name, default_subnet, provider_type)

    # Creating keys
    create_cred_keys(key_dir)

    # create scripts
    create_scripts(script_dir)


def main():
    service_name = "Hello"
    dir_name = os.getcwd()
    init_bp(service_name, dir_name)


if __name__ == "__main__":
    main()
