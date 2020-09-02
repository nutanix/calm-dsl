from .ref import Ref
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


# TODO Add validation on account passed as parameter is of same type as class
class Provider:
    def __new__(cls, *args, **kwargs):
        raise TypeError("'{}' is not callable".format(cls.__name__))

    class Ntnx:
        def __new__(cls, account, subnets=[]):

            # TODO add key check for `host_pc` instead of name
            host_pc = False
            if account["name"] == "NTNX_LOCAL_AZ":
                host_pc = True

            return {
                "provider_type": "nutanix_pc",
                "account_reference": account,
                "external_network_list": subnets if not host_pc else [],
                "subnet_reference_list": subnets if host_pc else [],
                "default_subnet_reference": subnets[0] if subnets else {},
            }

        class Local_Az:
            def __new__(cls, subnets=[]):

                # TODO add key check for `host_pc` instead of name
                account_name = "NTNX_LOCAL_AZ"
                account = Ref.Account(account_name)

                return {
                    "provider_type": "nutanix_pc",
                    "account_reference": account,
                    "subnet_reference_list": subnets,
                    "default_subnet_reference": subnets[0] if subnets else {},
                }

        class Remote_Az:
            def __new__(cls, account, subnets=[]):

                return {
                    "provider_type": "nutanix_pc",
                    "account_reference": account,
                    "external_network_list": subnets,
                    "default_subnet_reference": subnets[0] if subnets else {},
                }

    class Aws:
        def __new__(cls, account):
            return {"provider_type": "aws", "account_reference": account}

    class Azure:
        def __new__(cls, account):
            return {"provider_type": "azure", "account_reference": account}

    class Gcp:
        def __new__(cls, account):
            return {"provider_type": "gcp", "account_reference": account}

    class Vmware:
        def __new__(cls, account):
            return {"provider_type": "vmware", "account_reference": account}

    class K8s:
        def __new__(cls, account):
            return {"provider_type": "k8s", "account_reference": account}
