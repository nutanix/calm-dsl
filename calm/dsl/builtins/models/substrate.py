from .entity import EntityType, Entity
from .validator import PropertyValidator


# Substrate


class SubstrateType(EntityType):
    __schema_name__ = "Substrate"
    __openapi_type__ = "app_substrate"

    ALLOWED_FRAGMENT_ACTIONS = {
        "__pre_create__": "pre_action_create",
        "__post_delete__": "post_action_delete",
    }

    def compile(cls):

        cdict = super().compile()

        readiness_probe = {}
        if "readiness_probe" in cdict and cdict["readiness_probe"]:
            readiness_probe = cdict["readiness_probe"]
        if cdict["type"] == "AHV_VM":
            if not readiness_probe:
                readiness_probe = {
                    "address": "@@{platform.status.resources.nic_list[0].ip_endpoint_list[0].ip}@@",
                    "disable_readiness_probe": False,
                    "delay_secs": "0",
                    "connection_type": "SSH",
                    "connection_port": 22,
                    "connection_protocol": "",
                }
                if "os_type" in cdict and cdict["os_type"] == "Windows":
                    readiness_probe["connection_type"] = "POWERSHELL"
                    readiness_probe["connection_port"] = 5985
                    readiness_probe["connection_protocol"] = "http"
            elif not readiness_probe.get("address"):
                readiness_probe[
                    "address"
                ] = "@@{platform.status.resources.nic_list[0].ip_endpoint_list[0].ip}@@"

        elif cdict["type"] == "EXISTING_VM":
            if not readiness_probe:
                readiness_probe = {
                    "address": "@@{ip_address}@@",
                    "disable_readiness_probe": False,
                    "delay_secs": "0",
                    "connection_type": "SSH",
                    "connection_port": 22,
                    "connection_protocol": "",
                }
                if "os_type" in cdict and cdict["os_type"] == "Windows":
                    readiness_probe["connection_type"] = "POWERSHELL"
                    readiness_probe["connection_port"] = 5985
                    readiness_probe["connection_protocol"] = "http"
            elif not readiness_probe.get("address"):
                readiness_probe["address"] = "@@{ip_address}@@"

        elif cdict["type"] == "AWS_VM":
            if not readiness_probe:
                readiness_probe = {
                    "address": "@@{public_ip_address}@@",
                    "disable_readiness_probe": False,
                    "delay_secs": "60",
                    "connection_type": "SSH",
                    "connection_port": 22,
                    "connection_protocol": "",
                }
                if "os_type" in cdict and cdict["os_type"] == "Windows":
                    readiness_probe["connection_type"] = "POWERSHELL"
                    readiness_probe["connection_port"] = 5985
                    readiness_probe["connection_protocol"] = "http"
            elif not readiness_probe.get("address"):
                readiness_probe["address"] = "@@{public_ip_address}@@"

        elif cdict["type"] == "K8S_POD":  # Never used (Omit after discussion)
            readiness_probe = {
                "address": "",
                "disable_readiness_probe": False,
                "delay_secs": "60",
                "connection_type": "SSH",
                "connection_port": 22,
                "retries": "5",
            }
            cdict.pop("editables", None)

        elif cdict["type"] == "AZURE_VM":
            if not readiness_probe:
                readiness_probe = {
                    "connection_type": "SSH",
                    "retries": "5",
                    "connection_protocol": "",
                    "connection_port": 22,
                    "address": "@@{platform.publicIPAddressList[0]}@@",
                    "delay_secs": "60",
                    "disable_readiness_probe": False,
                }

                if "os_type" in cdict and cdict["os_type"] == "Windows":
                    readiness_probe["connection_type"] = "POWERSHELL"
                    readiness_probe["connection_port"] = 5985
                    readiness_probe["connection_protocol"] = "http"
            elif not readiness_probe.get("address"):
                readiness_probe["address"] = "@@{platform.publicIPAddressList[0]}@@"

        elif cdict["type"] == "VMWARE_VM":
            if not readiness_probe:
                readiness_probe = {
                    "connection_type": "SSH",
                    "retries": "5",
                    "connection_protocol": "",
                    "connection_port": 22,
                    "address": "@@{platform.ipAddressList[0]}@@",
                    "delay_secs": "60",
                    "disable_readiness_probe": False,
                }

                if "os_type" in cdict and cdict["os_type"] == "Windows":
                    readiness_probe["connection_type"] = "POWERSHELL"
                    readiness_probe["connection_port"] = 5985
                    readiness_probe["connection_protocol"] = "http"
            elif not readiness_probe.get("address"):
                readiness_probe["address"] = "@@{platform.ipAddressList[0]}@@"

        elif cdict["type"] == "GCP_VM":
            if not readiness_probe:
                readiness_probe = {
                    "connection_type": "SSH",
                    "retries": "5",
                    "connection_protocol": "",
                    "disable_readiness_probe": False,
                    "address": "@@{platform.networkInterfaces[0].networkIP}@@",
                    "delay_secs": "0",
                    "connection_port": 22,
                }

                if "os_type" in cdict and cdict["os_type"] == "Windows":
                    readiness_probe["connection_type"] = "POWERSHELL"
                    readiness_probe["connection_port"] = 5985
                    readiness_probe["connection_protocol"] = "http"
            elif not readiness_probe.get("address"):
                readiness_probe[
                    "address"
                ] = "@@{platform.networkInterfaces[0].networkIP}@@"
        else:
            raise Exception("Un-supported vm type :{}".format(cdict["type"]))

        cdict["readiness_probe"] = readiness_probe

        return cdict

    def get_task_target(cls):
        return cls.get_ref()


class SubstrateValidator(PropertyValidator, openapi_type="app_substrate"):
    __default__ = None
    __kind__ = SubstrateType


def substrate(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return SubstrateType(name, bases, kwargs)


Substrate = substrate()
