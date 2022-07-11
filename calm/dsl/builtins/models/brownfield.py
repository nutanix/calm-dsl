import sys

from .entity import EntityType, Entity
from .validator import PropertyValidator
from .deployment import DeploymentType
from .metadata_payload import get_metadata_obj

from .helper import common as common_helper
from calm.dsl.config import get_context
from calm.dsl.store import Cache
from calm.dsl.api import get_api_client
from calm.dsl.constants import CACHE, PROVIDER_ACCOUNT_TYPE_MAP
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def match_vm_data(
    vm_name,
    vm_address_list,
    vm_id,
    instance_name=None,
    instance_address=[],
    instance_id=None,
):
    """Returns True/False based on if vm data is matched with provided instance data"""

    if instance_id:  # Case when ip address is given
        if instance_id == vm_id:
            # If supplied ip_addresses not found in given instance, raise error
            if not set(instance_address).issubset(set(vm_address_list)):
                diff_ips = set(instance_address).difference(set(vm_address_list))
                LOG.error(
                    "IP Address {} not found in instance(id={})".format(diff_ips, vm_id)
                )
                sys.exit(-1)

            # If supplied name not matched with instance name, raise error
            if instance_name and instance_name != vm_name:
                LOG.error(
                    "Provided instance_name ({}) not matched with server instance name ({})".format(
                        instance_name, vm_name
                    )
                )
                sys.exit(-1)

            # If checks are correct, return True
            return True

    elif instance_address:  # Case when ip_address is given
        if set(instance_address).issubset(set(vm_address_list)):
            # If supplied name not matched with instance name, raise error
            if instance_name and instance_name != vm_name:
                LOG.error(
                    "Provided instance_name ({}) not matched with server instance name ({})".format(
                        instance_name, vm_name
                    )
                )
                sys.exit(-1)

            # If checks are correct, return True
            return True

    elif instance_name == vm_name:  # Case when instance_name is provided
        return True

    # If not matched by any check return False
    return False


# TODO merge provider specific helpers into one
def get_ahv_bf_vm_data(
    project_uuid, account_uuid, instance_name=None, ip_address=[], instance_id=None
):
    """Return ahv vm data matched with provided instacne details"""

    if not instance_id:
        if not (instance_name or ip_address):
            LOG.error("One of 'instance_name' or 'ip_address' must be given.")
            sys.exit(-1)

    client = get_api_client()
    res, err = client.account.read(account_uuid)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    res = res.json()
    clusters = res["status"]["resources"]["data"].get(
        "cluster_account_reference_list", []
    )
    if not clusters:
        LOG.error("No cluster found in ahv account (uuid='{}')".format(account_uuid))
        sys.exit(-1)

    # TODO Cluster should be a part of project whitelisted clusters. Change after jira is resolved
    # Jira: https://jira.nutanix.com/browse/CALM-20205
    cluster_uuid = clusters[0]["uuid"]

    params = {
        "length": 1000,
        "offset": 0,
        "filter": "project_uuid=={};account_uuid=={}".format(
            project_uuid, cluster_uuid
        ),
    }
    res, err = client.blueprint.brownfield_vms(params)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    res = res.json()
    if not res["metadata"]["total_matches"]:
        LOG.error(
            "No nutanix brownfield vms found on account(uuid='{}') and project(uuid='{}')".format(
                account_uuid, project_uuid
            )
        )
        sys.exit(-1)

    res_vm_data = None
    for entity in res["entities"]:
        e_resources = entity["status"]["resources"]
        e_name = e_resources["instance_name"]
        e_id = e_resources["instance_id"]
        e_address = e_resources["address"]
        e_address_list = e_resources["address_list"]

        if match_vm_data(
            vm_name=e_name,
            vm_address_list=e_address_list,
            vm_id=e_id,
            instance_name=instance_name,
            instance_address=ip_address,
            instance_id=instance_id,
        ):
            if res_vm_data:
                # If there is an existing vm with provided configuration
                LOG.error(
                    "Multiple vms with same name ({}) found".format(instance_name)
                )
                sys.exit(-1)

            res_vm_data = {
                "instance_name": e_name,
                "instance_id": e_id,
                "address": ip_address or e_address,
            }

    # If vm not found raise error
    if not res_vm_data:
        LOG.error(
            "No nutanix brownfield vm with details (name='{}', address='{}', id='{}') found on account(uuid='{}') and project(uuid='{}')".format(
                instance_name, ip_address, instance_id, account_uuid, project_uuid
            )
        )
        sys.exit(-1)

    return res_vm_data


def get_aws_bf_vm_data(
    project_uuid, account_uuid, instance_name=None, ip_address=[], instance_id=None
):
    """Return aws vm data matched with provided instacne details"""

    client = get_api_client()

    params = {
        "length": 250,
        "offset": 0,
        "filter": "project_uuid=={};account_uuid=={}".format(
            project_uuid, account_uuid
        ),
    }
    res, err = client.blueprint.brownfield_vms(params)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    res = res.json()
    if not res["metadata"]["total_matches"]:
        LOG.error(
            "No aws brownfield vms found on account(uuid='{}') and project(uuid='{}')".format(
                account_uuid, project_uuid
            )
        )
        sys.exit(-1)

    res_vm_data = None
    for entity in res["entities"]:
        e_resources = entity["status"]["resources"]
        e_name = e_resources["instance_name"]
        e_id = e_resources["instance_id"]
        e_address = e_resources["address"]
        e_address_list = e_resources["public_ip_address"]

        if match_vm_data(
            vm_name=e_name,
            vm_address_list=e_address_list,
            vm_id=e_id,
            instance_name=instance_name,
            instance_address=ip_address,
            instance_id=instance_id,
        ):
            if res_vm_data:
                # If there is an existing vm with provided configuration
                LOG.error(
                    "Multiple vms with same name ({}) found".format(instance_name)
                )
                sys.exit(-1)

            res_vm_data = {
                "instance_name": e_name,
                "instance_id": e_id,
                "address": ip_address or e_address,
            }

    # If vm not found raise error
    if not res_vm_data:
        LOG.error(
            "No aws brownfield vm with details (name='{}', address='{}', id='{}') found on account(uuid='{}') and project(uuid='{}')".format(
                instance_name, ip_address, instance_id, account_uuid, project_uuid
            )
        )
        sys.exit(-1)

    return res_vm_data


def get_azure_bf_vm_data(
    project_uuid, account_uuid, instance_name=None, ip_address=[], instance_id=None
):
    """Return azure vm data matched with provided instacne details"""

    client = get_api_client()

    if instance_name:
        filter = "instance_name=={};project_uuid=={};account_uuid=={}".format(
            instance_name, project_uuid, account_uuid
        )
    else:
        filter = "project_uuid=={};account_uuid=={}".format(project_uuid, account_uuid)
    params = {"length": 1000, "offset": 0, "filter": filter}
    res, err = client.blueprint.brownfield_vms(params)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    res = res.json()
    if not res["metadata"]["total_matches"]:
        LOG.error(
            "No azure brownfield vms found on account(uuid='{}') and project(uuid='{}')".format(
                account_uuid, project_uuid
            )
        )
        sys.exit(-1)

    res_vm_data = None
    for entity in res["entities"]:
        e_resources = entity["status"]["resources"]
        e_name = e_resources["instance_name"]
        e_id = e_resources["instance_id"]
        e_address = e_resources["address"]
        e_address_list = e_resources["public_ip_address"]
        e_private_address = e_resources["private_ip_address"]
        if (not e_address_list) and e_private_address:
            e_address = [e_private_address]
            e_address_list = e_private_address

        if match_vm_data(
            vm_name=e_name,
            vm_address_list=e_address_list,
            vm_id=e_id,
            instance_name=instance_name,
            instance_address=ip_address,
            instance_id=instance_id,
        ):
            if res_vm_data:
                # If there is an existing vm with provided configuration
                LOG.error(
                    "Multiple vms with same name ({}) found".format(instance_name)
                )
                sys.exit(-1)

            res_vm_data = {
                "instance_name": e_name,
                "instance_id": e_id,
                "address": ip_address or e_address,
                "platform_data": {"resource_group": e_resources["resource_group"]},
            }

    # If vm not found raise error
    if not res_vm_data:
        LOG.error(
            "No azure brownfield vm with details (name='{}', address='{}', id='{}') found on account(uuid='{}') and project(uuid='{}')".format(
                instance_name, ip_address, instance_id, account_uuid, project_uuid
            )
        )
        sys.exit(-1)

    return res_vm_data


def get_vmware_bf_vm_data(
    project_uuid, account_uuid, instance_name=None, ip_address=[], instance_id=None
):
    """Return vmware vm data matched with provided instacne details"""

    client = get_api_client()

    params = {
        "length": 250,
        "offset": 0,
        "filter": "project_uuid=={};account_uuid=={}".format(
            project_uuid, account_uuid
        ),
    }
    res, err = client.blueprint.brownfield_vms(params)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    res = res.json()
    if not res["metadata"]["total_matches"]:
        LOG.error(
            "No vmware brownfield vms found on account(uuid='{}') and project(uuid='{}')".format(
                account_uuid, project_uuid
            )
        )
        sys.exit(-1)

    res_vm_data = None
    for entity in res["entities"]:
        e_resources = entity["status"]["resources"]
        e_name = e_resources["instance_name"]
        e_id = e_resources["instance_id"]
        e_address = e_resources["address"]
        e_address_list = e_resources["guest.ipAddress"]

        if match_vm_data(
            vm_name=e_name,
            vm_address_list=e_address_list,
            vm_id=e_id,
            instance_name=instance_name,
            instance_address=ip_address,
            instance_id=instance_id,
        ):
            if res_vm_data:
                # If there is an existing vm with provided configuration
                LOG.error(
                    "Multiple vms with same name ({}) found".format(instance_name)
                )
                sys.exit(-1)

            res_vm_data = {
                "instance_name": e_name,
                "instance_id": e_id,
                "address": ip_address or e_address,
            }

    # If vm not found raise error
    if not res_vm_data:
        LOG.error(
            "No vmware brownfield vm with details (name='{}', address='{}', id='{}') found on account(uuid='{}') and project(uuid='{}')".format(
                instance_name, ip_address, instance_id, account_uuid, project_uuid
            )
        )
        sys.exit(-1)

    return res_vm_data


def get_gcp_bf_vm_data(
    project_uuid, account_uuid, instance_name=None, ip_address=[], instance_id=None
):
    """Return gcp vm data matched with provided instacne details"""

    client = get_api_client()

    params = {
        "length": 250,
        "offset": 0,
        "filter": "project_uuid=={};account_uuid=={}".format(
            project_uuid, account_uuid
        ),
    }
    res, err = client.blueprint.brownfield_vms(params)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    res = res.json()
    if not res["metadata"]["total_matches"]:
        LOG.error(
            "No gcp brownfield vms found on account(uuid='{}') and project(uuid='{}')".format(
                account_uuid, project_uuid
            )
        )
        sys.exit(-1)

    res_vm_data = None
    for entity in res["entities"]:
        e_resources = entity["status"]["resources"]
        e_name = e_resources["instance_name"]
        e_id = e_resources["id"]
        e_address = e_resources["address"]
        e_address_list = e_resources["natIP"]

        if match_vm_data(
            vm_name=e_name,
            vm_address_list=e_address_list,
            vm_id=e_id,
            instance_name=instance_name,
            instance_address=ip_address,
            instance_id=instance_id,
        ):
            if res_vm_data:
                # If there is an existing vm with provided configuration
                LOG.error(
                    "Multiple vms with same name ({}) found".format(instance_name)
                )
                sys.exit(-1)

            res_vm_data = {
                "instance_name": e_name,
                "instance_id": e_id,
                "address": ip_address or e_address,
            }

    # If vm not found raise error
    if not res_vm_data:
        LOG.error(
            "No gcp brownfield vm with details (name='{}', address='{}', id='{}') found on account(uuid='{}') and project(uuid='{}')".format(
                instance_name, ip_address, instance_id, account_uuid, project_uuid
            )
        )
        sys.exit(-1)

    return res_vm_data


# Brownfield Vm


class BrownfiedVmType(EntityType):
    __schema_name__ = "BrownfieldVm"
    __openapi_type__ = "app_brownfield_vm"

    def get_profile_environment(cls):
        """
        returns the env configuration if present at brownfield vm's profile
        """

        environment = {}
        cls_profile = common_helper._walk_to_parent_with_given_type(cls, "ProfileType")
        environment = getattr(cls_profile, "environment", {})
        if environment:
            LOG.debug(
                "Found environment {} associated to app-profile {}".format(
                    environment.get("name"), cls_profile
                )
            )
        else:
            LOG.debug(
                "No environment associated to the app-profile {}".format(cls_profile)
            )

        if environment:
            environment = Cache.get_entity_data_using_uuid(
                entity_type=CACHE.ENTITY.ENVIRONMENT, uuid=environment["uuid"]
            )

        return environment

    def get_substrate(cls):
        """return substrate attached to brownfield vm's deployment"""

        cls_deployment = common_helper._walk_to_parent_with_given_type(
            cls, "BrownfieldDeploymentType"
        )

        if cls_deployment and getattr(cls_deployment, "substrate", None):
            return cls_deployment.substrate.__self__

        return None

    def get_account_uuid(cls):
        """returns the account_uuid configured for given brwonfield vm"""

        project_cache_data = common_helper.get_cur_context_project()
        environment_cache_data = cls.get_profile_environment()
        cls_substrate = cls.get_substrate()

        provider_type = cls.provider

        # account_uuid is attached to brownfield instances if a
        # blueprint is launched with runtime brownfield deployments
        account_uuid = getattr(cls, "account_uuid", "")
        if cls_substrate:
            account = getattr(cls_substrate, "account", dict()) or dict()
            if account:
                account_uuid = account["uuid"]

        if not account_uuid:
            if environment_cache_data:
                accounts = environment_cache_data["accounts_data"].get(
                    PROVIDER_ACCOUNT_TYPE_MAP[provider_type], []
                )
                if not accounts:
                    LOG.error(
                        "No {} account regsitered in environment".format(provider_type)
                    )
                    sys.exit(-1)

            else:
                accounts = project_cache_data["accounts_data"].get(
                    PROVIDER_ACCOUNT_TYPE_MAP[provider_type], []
                )
                if not accounts:
                    LOG.error(
                        "No {} account regsitered in environment".format(provider_type)
                    )
                    sys.exit(-1)

            account_uuid = accounts[0]

        return account_uuid

    def compile(cls):

        cdict = super().compile()
        provider_type = cdict.pop("provider")

        project_cache_data = common_helper.get_cur_context_project()
        account_uuid = cls.get_account_uuid()

        project_uuid = project_cache_data.get("uuid")

        if provider_type == "AHV_VM":
            cdict = get_ahv_bf_vm_data(
                project_uuid=project_uuid,
                account_uuid=account_uuid,
                instance_name=cdict["instance_name"],
                ip_address=cdict["address"],
                instance_id=cdict["instance_id"],
            )

        elif provider_type == "AWS_VM":
            cdict = get_aws_bf_vm_data(
                project_uuid=project_uuid,
                account_uuid=account_uuid,
                instance_name=cdict["instance_name"],
                ip_address=cdict["address"],
                instance_id=cdict["instance_id"],
            )

        elif provider_type == "AZURE_VM":
            cdict = get_azure_bf_vm_data(
                project_uuid=project_uuid,
                account_uuid=account_uuid,
                instance_name=cdict["instance_name"],
                ip_address=cdict["address"],
                instance_id=cdict["instance_id"],
            )

        elif provider_type == "VMWARE_VM":
            cdict = get_vmware_bf_vm_data(
                project_uuid=project_uuid,
                account_uuid=account_uuid,
                instance_name=cdict["instance_name"],
                ip_address=cdict["address"],
                instance_id=cdict["instance_id"],
            )

        elif provider_type == "GCP_VM":
            cdict = get_gcp_bf_vm_data(
                project_uuid=project_uuid,
                account_uuid=account_uuid,
                instance_name=cdict["instance_name"],
                ip_address=cdict["address"],
                instance_id=cdict["instance_id"],
            )

        else:
            LOG.error(
                "Support for {} provider's brownfield vm not available".format(
                    provider_type
                )
            )
            sys.exit(-1)

        return cdict


class BrownfieldVmValidator(PropertyValidator, openapi_type="app_brownfield_vm"):
    __default__ = None
    __kind__ = BrownfiedVmType


def brownfield_vm(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return BrownfiedVmType(name, bases, kwargs)


# Brownfield Deployment


class BrownfieldDeploymentType(DeploymentType):
    __schema_name__ = "BrownfieldDeployment"
    __openapi_type__ = "app_brownfield_deployment"

    def get_ref(cls, kind=None):
        """Note: app_blueprint_deployment kind to be used for pod deployment"""
        return super().get_ref(kind=DeploymentType.__openapi_type__)

    def compile(cls):
        cdict = super().compile()

        # Constants from UI
        cdict["min_replicas"] = "1"
        cdict["max_replicas"] = "1"
        return cdict


class BrownfieldDeploymentValidator(
    PropertyValidator, openapi_type="app_brownfield_deployment"
):
    __default__ = None
    __kind__ = BrownfieldDeploymentType


def brownfield_deployment(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return BrownfieldDeploymentType(name, bases, kwargs)


BrownfieldDeployment = brownfield_deployment()


class Brownfield:
    Deployment = BrownfieldDeployment

    class Vm:
        def __new__(cls, instance_name=None, ip_address=[], instance_id=None):
            """Vms are searched using these ways:
            1. If instance_id is given will search using that
            2. Else Search using ip_address if given
            3. Else Search using name
            """

            kwargs = {
                "instance_name": instance_name,
                "address": ip_address,
                "instance_id": instance_id,
                "provider": "AHV_VM",
            }
            return brownfield_vm(**kwargs)

        class Ahv:
            def __new__(cls, instance_name=None, ip_address=[], instance_id=None):
                """Vms are searched using these ways:
                1. If instance_id is given will search using that
                2. Else Search using ip_address if given
                3. Else Search using name
                """

                kwargs = {
                    "instance_name": instance_name,
                    "address": ip_address,
                    "instance_id": instance_id,
                    "provider": "AHV_VM",
                }
                return brownfield_vm(**kwargs)

        class Aws:
            def __new__(cls, instance_name=None, ip_address=[], instance_id=None):
                """Vms are searched using these ways:
                1. If instance_id is given will search using that
                2. Else Search using ip_address if given
                3. Else Search using name
                """

                kwargs = {
                    "instance_name": instance_name,
                    "address": ip_address,
                    "instance_id": instance_id,
                    "provider": "AWS_VM",
                }
                return brownfield_vm(**kwargs)

        class Azure:
            def __new__(cls, instance_name=None, ip_address=[], instance_id=None):
                """Vms are searched using these ways:
                1. If instance_id is given will search using that
                2. Else Search using ip_address if given
                3. Else Search using name
                """

                kwargs = {
                    "instance_name": instance_name,
                    "address": ip_address,
                    "instance_id": instance_id,
                    "provider": "AZURE_VM",
                }
                return brownfield_vm(**kwargs)

        class Gcp:
            def __new__(cls, instance_name=None, ip_address=[], instance_id=None):
                """Vms are searched using these ways:
                1. If instance_id is given will search using that
                2. Else Search using ip_address if given
                3. Else Search using name
                """

                kwargs = {
                    "instance_name": instance_name,
                    "address": ip_address,
                    "instance_id": instance_id,
                    "provider": "GCP_VM",
                }
                return brownfield_vm(**kwargs)

        class Vmware:
            def __new__(cls, instance_name=None, ip_address=[], instance_id=None):
                """Vms are searched using these ways:
                1. If instance_id is given will search using that
                2. Else Search using ip_address if given
                3. Else Search using name
                """

                kwargs = {
                    "instance_name": instance_name,
                    "address": ip_address,
                    "instance_id": instance_id,
                    "provider": "VMWARE_VM",
                }
                return brownfield_vm(**kwargs)
