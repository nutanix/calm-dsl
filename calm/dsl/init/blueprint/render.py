import os
from io import StringIO
from jinja2 import Environment, PackageLoader
from Crypto.PublicKey import RSA

from calm.dsl.config import get_config
from calm.dsl.api import get_api_client
from calm.dsl.config import get_config
from calm.dsl.store import Cache


def render_blueprint_template(service_name, subnet_name, schema_file="blueprint.py.jinja2"):

    service_name = service_name.strip().split()[0].title()

    loader = PackageLoader(__name__, "")
    env = Environment(loader=loader)
    template = env.get_template(schema_file)
    text = template.render(service_name=service_name, subnet_name=subnet_name)
    return text.strip() + "\n"


def create_bp_file(dir_name, service_name, subnet_name):

    bp_text = render_blueprint_template(service_name, subnet_name)

    bp_path = os.path.join(dir_name, "blueprint.py")

    with open(bp_path, "w") as fd:
        fd.write(bp_text)


def create_cred_keys(dir_name):

    # Will create key via name centos/centos_pub
    
    key = RSA.generate(2048)
    private_key = key.export_key()
    file_out = open("{}/centos".format(dir_name), "wb")
    file_out.write(private_key)

    public_key = key.publickey().export_key()
    file_out = open("{}/centos_pub".format(dir_name), "wb")
    file_out.write(public_key)


def make_bp_dirs(dir_name, bp_name):

     # Note for creating directory we have to provide the path for file
     # So adding random.txt
     bp_dir = "{}/{}". format(dir_name, bp_name)
     if not os.path.isdir(bp_dir):
        os.makedirs(bp_dir)

     local_dir = "{}/{}". format(bp_dir, ".local")
     if not os.path.isdir(local_dir):
        os.makedirs(local_dir)

     key_dir = "{}/{}". format(local_dir, "keys")
     if not os.path.isdir(key_dir):
        os.makedirs(key_dir)
        
     script_dir = "{}/{}". format(bp_dir, "scripts")
     if not os.path.isdir(script_dir):
        os.makedirs(script_dir)

     return (bp_dir, local_dir, key_dir, script_dir)


def init_bp(service_name, dir_name):

    bp_name = "{}Blueprint". format(service_name, )

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

    subnets = res["status"]["project_status"]["resources"].get("subnet_reference_list", [])
    if not subnets:
        raise Exception("no subnets registered !!!")

    default_subnet = subnets[0]["name"]

    create_bp_file(bp_dir, service_name, default_subnet)

    # Creating keys
    create_cred_keys(key_dir)


def main():
    service_name = "Hello"
    dir_name = os.getcwd()
    init_bp(service_name, dir_name)


if __name__ == "__main__":
    main()
