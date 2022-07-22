from .entity import Entity, EntityType
from .validator import PropertyValidator
from .calm_ref import Ref
from calm.dsl.log import get_logging_handle


LOG = get_logging_handle(__name__)


class AccountProviderType(EntityType):
    __schema_name__ = "AccountProvider"
    __openapi_type__ = "app_account_provider"


class AccountProviderValidator(PropertyValidator, openapi_type="app_account_provider"):
    __default__ = None
    __kind__ = AccountProviderType


def account_provider(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return AccountProviderType(name, bases, kwargs)


# TODO Add validation on account passed as parameter is of same type as class
class Provider:
    def __new__(cls, *args, **kwargs):
        raise TypeError("'{}' is not callable".format(cls.__name__))

    class Ntnx:
        def __new__(cls, account, subnets=[], clusters=[], vpcs=[]):
            # TODO add key check for `host_pc` instead of name
            host_pc = False
            if account["name"] == "NTNX_LOCAL_AZ":
                host_pc = True

            return account_provider(
                type="nutanix_pc",
                account_reference=account,
                external_network_list=subnets if not host_pc else [],
                subnet_reference_list=subnets if host_pc else [],
                default_subnet_reference=subnets[0] if subnets else {},
                cluster_reference_list=clusters,
                vpc_reference_list=vpcs,
            )

        class Local_Az:
            def __new__(cls, subnets=[], clusters=[], vpcs=[]):

                # TODO add key check for `host_pc` instead of name
                account_name = "NTNX_LOCAL_AZ"
                account = Ref.Account(account_name)

                return account_provider(
                    type="nutanix_pc",
                    account_reference=account,
                    subnet_reference_list=subnets,
                    default_subnet_reference=subnets[0] if subnets else {},
                    cluster_reference_list=clusters,
                    vpc_reference_list=vpcs,
                )

        class Remote_Az:
            def __new__(cls, account, subnets=[], clusters=[], vpcs=[]):

                return account_provider(
                    type="nutanix_pc",
                    account_reference=account,
                    external_network_list=subnets,
                    default_subnet_reference=subnets[0] if subnets else {},
                    cluster_reference_list=clusters,
                    vpc_reference_list=vpcs,
                )

    class Aws:
        def __new__(cls, account):
            return account_provider(type="aws", account_reference=account)

    class Azure:
        def __new__(cls, account):
            return account_provider(type="azure", account_reference=account)

    class Gcp:
        def __new__(cls, account):
            return account_provider(type="gcp", account_reference=account)

    class Vmware:
        def __new__(cls, account):
            return account_provider(type="vmware", account_reference=account)

    class K8s:
        def __new__(cls, account):
            return account_provider(type="k8s", account_reference=account)

    class Custom_Provider:
        def __new__(cls, account):
            return account_provider(type="custom_provider", account_reference=account)
