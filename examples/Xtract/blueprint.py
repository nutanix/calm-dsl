"""
Xtract Blueprint

"""

from calm.dsl.builtins import SimpleDeployment, SimpleBlueprint
from calm.dsl.builtins import read_provider_spec
from calm.dsl.builtins import basic_cred
from calm.dsl.builtins import CalmVariable as Var
from calm.dsl.builtins import read_local_file


ADMIN_PASSWD = read_local_file("admin_passwd")


class XtractDeployment(SimpleDeployment):
    """Xtract Deployment"""

    provider_spec = read_provider_spec("ahv_spec.yaml")


class XtractDslBlueprint(SimpleBlueprint):
    """Xtract Blueprint"""

    credentials = [basic_cred("admin", ADMIN_PASSWD, name="default cred", default=True)]
    nameserver = Var("10.40.64.15", label="Local DNS resolver")
    deployments = [XtractDeployment]


def main():
    import json

    bp_dict = XtractDslBlueprint.make_single_vm_bp_dict()
    generated_json = json.dumps(bp_dict, indent=4)

    print(generated_json)


if __name__ == "__main__":
    main()
