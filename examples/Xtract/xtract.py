"""
Xtract Blueprint

"""

from calm.dsl.builtins import ref, basic_cred
from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import Deployment, Profile, Blueprint
from calm.dsl.builtins import read_provider_spec, read_local_file


ADMIN_PASSWD = read_local_file("admin_passwd")

DefaultCred = basic_cred("admin", ADMIN_PASSWD, name="default cred", default=True)


class XtractVM(Service):
    """Xtract service"""

    pass


class XtractPackage(Package):
    """Xtract package"""

    services = [ref(XtractVM)]


class XtractVMS(Substrate):
    """Xtract Substrate"""

    provider_spec = read_provider_spec("ahv_spec.yaml")
    readiness_probe = {
        "disabled": True,
        "delay_secs": "0",
        "connection_type": "SSH",
        "connection_port": 22,
        "credential": ref(DefaultCred),
    }


class XtractDeployment(Deployment):
    """Xtract Deployment"""

    packages = [ref(XtractPackage)]
    substrate = ref(XtractVMS)


class AHV(Profile):
    """Xtract Profile"""

    deployments = [XtractDeployment]


class XtractDslBlueprint(Blueprint):
    """* [Xtract for VMs](https://@@{XtractVM.address}@@)"""

    credentials = [DefaultCred]
    services = [XtractVM]
    packages = [XtractPackage]
    substrates = [XtractVMS]
    profiles = [AHV]


def main():
    print(XtractDslBlueprint.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
