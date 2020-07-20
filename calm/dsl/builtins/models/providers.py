import sys

from .entity import EntityType, Entity
from .validator import PropertyValidator
from calm.dsl.store import Cache
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def get_account_ref(name):
    provider_data = Cache.get_entity_data(entity_type="account", name=name)
    if not provider_data:
        LOG.error("Provider Account '{}' not found. Please update cache".format(name))
        sys.exit(-1)

    return {"kind": "account", "name": name, "uuid": provider_data["uuid"]}


class Provider:
    def __new__(cls, *args, **kwargs):
        raise TypeError("'{}' is not callable".format(cls.__name__))

    class Ntnx:
        def __new__(cls, name, subnets=[]):
            account_ref = get_account_ref(name=name)
            return {
                "provider_type": "nutanix_pc",
                "account_reference": account_ref,
            }

        class Local_Az:
            def __new__(cls, subnets=[]):
                # TODO add key check for `host_pc` instead of name
                account_ref = get_account_ref(name="NTNX_LOCAL_AZ")
                return {
                    "provider_type": "nutanix_pc",
                    "account_reference": account_ref,
                }

    class Aws:
        def __new__(cls, name):
            account_ref = get_account_ref(name=name)
            return {
                "provider_type": "aws",
                "account_reference": account_ref,
            }

    class Azure:
        def __new__(cls, name):
            account_ref = get_account_ref(name=name)
            return {
                "provider_type": "azure",
                "account_reference": account_ref,
            }

    class Gcp:
        def __new__(cls, name):
            account_ref = get_account_ref(name=name)
            return {
                "provider_type": "gcp",
                "account_reference": account_ref,
            }

    class Vmware:
        def __new__(cls, name):
            account_ref = get_account_ref(name=name)
            return {
                "provider_type": "vmware",
                "account_reference": account_ref,
            }

    class K8s:
        def __new__(cls, name):
            account_ref = get_account_ref(name=name)
            return {
                "provider_type": "k8s",
                "account_reference": account_ref,
            }
