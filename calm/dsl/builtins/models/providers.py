import sys

from .entity import EntityType, Entity
from .validator import PropertyValidator
from calm.dsl.store import Cache
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def get_account_ref(name, provider_type):
    provider_data = Cache.get_entity_data(
        entity_type="account", name=name, provider_type=provider_type
    )
    if not provider_data:
        LOG.error(
            "Account '{}' of provider({}) not found. Please update cache".format(
                name, provider_type
            )
        )
        sys.exit(-1)

    return {"kind": "account", "name": name, "uuid": provider_data["uuid"]}


def get_ntnx_provider_data(name, host_pc=False, subnets=[], default_subnet=0):

    account_ref = get_account_ref(name=name, provider_type="nutanix_pc")
    account_uuid = account_ref["uuid"]
    subnet_ref_list = []
    for subnet_obj in subnets:
        subnet_data = Cache.get_entity_data(
            entity_type="ahv_subnet",
            name=subnet_obj["name"],
            cluster=subnet_obj["cluster"],
            account_uuid=account_uuid,
        )

        if not subnet_data:
            LOG.error(
                "Subnet('{}') with cluster('{}') not found. Please update cache".format(
                    subnet_obj["name"], subnet_obj["cluster"]
                )
            )
            sys.exit(-1)

        subnet_ref_list.append(
            {"name": subnet_data["name"], "kind": "subnet", "uuid": subnet_data["uuid"]}
        )

    if not subnet_ref_list:
        return {
            "provider_type": "nutanix_pc",
            "account_reference": account_ref,
        }

    else:
        if default_subnet < 0 or default_subnet >= len(subnet_ref_list):
            LOG.error(
                "Default subnet index({}) should be between >=0 and <{}".format(
                    default_subnet, len(subnet_ref_list)
                )
            )
            sys.exit(-1)

        if host_pc:
            return {
                "provider_type": "nutanix_pc",
                "account_reference": account_ref,
                "subnet_reference_list": subnet_ref_list,
                "default_subnet_reference": subnet_ref_list[default_subnet],
            }

        else:
            return {
                "provider_type": "nutanix_pc",
                "account_reference": account_ref,
                "external_network_list": subnet_ref_list,
                "default_subnet_reference": subnet_ref_list[default_subnet],
            }


class Provider:
    def __new__(cls, *args, **kwargs):
        raise TypeError("'{}' is not callable".format(cls.__name__))

    class Ntnx:
        def __new__(cls, name, subnets=[], default_subnet=0):

            # TODO add key check for `host_pc` instead of name
            if name == "NTNX_LOCAL_AZ":
                return get_ntnx_provider_data(
                    name=name,
                    subnets=subnets,
                    default_subnet=default_subnet,
                    host_pc=True,
                )

            else:
                return get_ntnx_provider_data(
                    name=name,
                    subnets=subnets,
                    default_subnet=default_subnet,
                    host_pc=False,
                )

        class Local_Az:
            def __new__(cls, subnets=[], default_subnet=0):

                # TODO add key check for `host_pc` instead of name
                return get_ntnx_provider_data(
                    name="NTNX_LOCAL_AZ",
                    subnets=subnets,
                    default_subnet=default_subnet,
                    host_pc=True,
                )

        class Remote_Az:
            def __new__(cls, name, subnets=[], default_subnet=0):

                # TODO add check whether local_az account is not supplied
                return get_ntnx_provider_data(
                    name=name,
                    subnets=subnets,
                    default_subnet=default_subnet,
                    host_pc=False,
                )

    class Aws:
        def __new__(cls, name):
            account_ref = get_account_ref(name=name, provider_type="aws")
            return {
                "provider_type": "aws",
                "account_reference": account_ref,
            }

    class Azure:
        def __new__(cls, name):
            account_ref = get_account_ref(name=name, provider_type="azure")
            return {
                "provider_type": "azure",
                "account_reference": account_ref,
            }

    class Gcp:
        def __new__(cls, name):
            account_ref = get_account_ref(name=name, provider_type="gcp")
            return {
                "provider_type": "gcp",
                "account_reference": account_ref,
            }

    class Vmware:
        def __new__(cls, name):
            account_ref = get_account_ref(name=name, provider_type="vmware")
            return {
                "provider_type": "vmware",
                "account_reference": account_ref,
            }

    class K8s:
        def __new__(cls, name):
            account_ref = get_account_ref(name=name, provider_type="k8s")
            return {
                "provider_type": "k8s",
                "account_reference": account_ref,
            }
