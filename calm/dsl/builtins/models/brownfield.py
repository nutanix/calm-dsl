import sys

from .entity import EntityType, Entity
from .validator import PropertyValidator
from .deployment import DeploymentType
from .metadata_payload import get_metadata_obj

from calm.dsl.config import get_config
from calm.dsl.store import Cache
from calm.dsl.api import get_api_client, get_resource_api
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


# TODO merge provider specific helpers into one
def get_ahv_bf_vm_data(
    project_uuid, account_uuid, instance_name, ip_address=[], instance_id=None
):

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

    cluster_uuid = clusters[0]["uuid"]

    params = {
        "length": 250,
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

    for entity in res["entities"]:
        e_resources = entity["status"]["resources"]
        if e_resources["instance_name"] == instance_name:
            if instance_id and e_resources["instance_id"] != instance_id:
                continue

            if ip_address and not set(ip_address).issubset(e_resources["address_list"]):
                continue

            ip_address = ip_address or e_resources["address"]
            instance_id = e_resources["instance_id"]

            return {
                "instance_name": instance_name,
                "instance_id": instance_id,
                "address": list(ip_address),
            }

    # If not vm found raise error
    LOG.error(
        "No nutanix brownfield vm (name='{}') found on account(uuid='{}') and project(uuid='{}')".format(
            instance_name, account_uuid, project_uuid
        )
    )
    sys.exit(-1)


def get_aws_bf_vm_data(
    project_uuid, account_uuid, instance_name, ip_address=[], instance_id=None
):

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

    for entity in res["entities"]:
        e_resources = entity["status"]["resources"]
        if e_resources["instance_name"] == instance_name:
            if instance_id and e_resources["instance_id"] != instance_id:
                continue

            if ip_address and not set(ip_address).issubset(
                e_resources["public_ip_address"]
            ):
                continue

            ip_address = ip_address or e_resources["address"]
            instance_id = e_resources["instance_id"]

            return {
                "instance_name": instance_name,
                "instance_id": instance_id,
                "address": list(ip_address),
            }

    # If not vm found raise error
    LOG.error(
        "No aws brownfield vm (name='{}') found on account(uuid='{}') and project(uuid='{}')".format(
            instance_name, account_uuid, project_uuid
        )
    )
    sys.exit(-1)


def get_azure_bf_vm_data(
    project_uuid, account_uuid, instance_name, ip_address=[], instance_id=None
):

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
            "No azure brownfield vms found on account(uuid='{}') and project(uuid='{}')".format(
                account_uuid, project_uuid
            )
        )
        sys.exit(-1)

    for entity in res["entities"]:
        e_resources = entity["status"]["resources"]
        if e_resources["instance_name"] == instance_name:
            if instance_id and e_resources["instance_id"] != instance_id:
                continue

            if ip_address and not set(ip_address).issubset(e_resources["address"]):
                continue

            ip_address = ip_address or e_resources["address"]
            instance_id = e_resources["instance_id"]

            return {
                "instance_name": instance_name,
                "instance_id": instance_id,
                "address": list(ip_address),
                "platform_data": {"resource_group": e_resources["resource_group"]},
            }

    # If not vm found raise error
    LOG.error(
        "No azure brownfield vm (name='{}') found on account(uuid='{}') and project(uuid='{}')".format(
            instance_name, account_uuid, project_uuid
        )
    )
    sys.exit(-1)


def get_vmware_bf_vm_data(
    project_uuid, account_uuid, instance_name, ip_address=[], instance_id=None
):

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

    for entity in res["entities"]:
        e_resources = entity["status"]["resources"]
        if e_resources["instance_name"] == instance_name:
            if instance_id and e_resources["instance_id"] != instance_id:
                continue

            if ip_address and not set(ip_address).issubset(
                e_resources["guest.ipAddress"]
            ):
                continue

            ip_address = ip_address or e_resources["address"]
            instance_id = e_resources["instance_id"]

            return {
                "instance_name": instance_name,
                "instance_id": instance_id,
                "address": list(ip_address),
                "platform_data": {},
            }

    # If not vm found raise error
    LOG.error(
        "No vmware brownfield vm (name='{}') found on account(uuid='{}') and project(uuid='{}')".format(
            instance_name, account_uuid, project_uuid
        )
    )
    sys.exit(-1)


def get_gcp_bf_vm_data(
    project_uuid, account_uuid, instance_name, ip_address=[], instance_id=None
):

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

    for entity in res["entities"]:
        e_resources = entity["status"]["resources"]
        if e_resources["instance_name"] == instance_name:
            if instance_id and e_resources["id"] != instance_id:
                continue

            if ip_address and not set(ip_address).issubset(e_resources["natIP"]):
                continue

            ip_address = ip_address or e_resources["address"]
            instance_id = e_resources["id"]

            return {
                "instance_name": instance_name,
                "instance_id": instance_id,
                "address": list(ip_address),
                "platform_data": {"zone": e_resources["zone"]},
            }

    # If not vm found raise error
    LOG.error(
        "No gcp brownfield vm (name='{}') found on account(uuid='{}') and project(uuid='{}')".format(
            instance_name, account_uuid, project_uuid
        )
    )
    sys.exit(-1)


# Brownfield Vm


class BrownfiedVmType(EntityType):
    __schema_name__ = "BrownfieldVm"
    __openapi_type__ = "app_brownfield_vm"

    def compile(cls):
        cdict = super().compile()
        provider_type = cdict.pop("provider")

        # Get project details
        client = get_api_client()
        config = get_config()

        # Getting the metadata obj
        metadata_obj = get_metadata_obj()
        project_ref = metadata_obj.get("project_reference") or dict()

        # If project not found in metadata, it will take project from config
        project_name = project_ref.get("name", config["PROJECT"]["name"])

        project_cache_data = Cache.get_entity_data(
            entity_type="project", name=project_name
        )
        if not project_cache_data:
            LOG.error(
                "Project {} not found. Please run: calm update cache".format(
                    project_name
                )
            )
            sys.exit(-1)

        project_uuid = project_cache_data.get("uuid")
        project_accounts = project_cache_data["accounts_data"]

        if provider_type == "AHV_VM":
            account_uuid = project_accounts.get("nutanix_pc", "")
            if not account_uuid:
                LOG.error(
                    "No ahv account registered in project '{}'".format(project_name)
                )
                sys.exit(-1)

            cdict = get_ahv_bf_vm_data(
                project_uuid=project_uuid,
                account_uuid=account_uuid,
                instance_name=cdict["instance_name"],
                ip_address=cdict["address"],
                instance_id=cdict["instance_id"],
            )

        elif provider_type == "AWS_VM":
            account_uuid = project_accounts.get("aws", "")
            if not account_uuid:
                LOG.error(
                    "No aws account registered in project '{}'".format(project_name)
                )
                sys.exit(-1)

            cdict = get_aws_bf_vm_data(
                project_uuid=project_uuid,
                account_uuid=account_uuid,
                instance_name=cdict["instance_name"],
                ip_address=cdict["address"],
                instance_id=cdict["instance_id"],
            )

        elif provider_type == "AZURE_VM":
            account_uuid = project_accounts.get("azure", "")
            if not account_uuid:
                LOG.error(
                    "No azure account registered in project '{}'".format(project_name)
                )
                sys.exit(-1)

            cdict = get_azure_bf_vm_data(
                project_uuid=project_uuid,
                account_uuid=account_uuid,
                instance_name=cdict["instance_name"],
                ip_address=cdict["address"],
                instance_id=cdict["instance_id"],
            )

        elif provider_type == "VMWARE_VM":
            account_uuid = project_accounts.get("vmware", "")
            if not account_uuid:
                LOG.error(
                    "No vmware account registered in project '{}'".format(project_name)
                )
                sys.exit(-1)

            cdict = get_vmware_bf_vm_data(
                project_uuid=project_uuid,
                account_uuid=account_uuid,
                instance_name=cdict["instance_name"],
                ip_address=cdict["address"],
                instance_id=cdict["instance_id"],
            )

        elif provider_type == "GCP_VM":
            account_uuid = project_accounts.get("gcp", "")
            if not account_uuid:
                LOG.error(
                    "No gcp account registered in project '{}'".format(project_name)
                )
                sys.exit(-1)

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
        def __new__(cls, instance_name, ip_address=[], instance_id=None):
            kwargs = {
                "instance_name": instance_name,
                "address": ip_address,
                "instance_id": instance_id,
                "provider": "AHV_VM",
            }
            return brownfield_vm(**kwargs)

        class Ahv:
            def __new__(cls, instance_name, ip_address=[], instance_id=None):
                kwargs = {
                    "instance_name": instance_name,
                    "address": ip_address,
                    "instance_id": instance_id,
                    "provider": "AHV_VM",
                }
                return brownfield_vm(**kwargs)

        class Aws:
            def __new__(cls, instance_name, ip_address=[], instance_id=None):
                kwargs = {
                    "instance_name": instance_name,
                    "address": ip_address,
                    "instance_id": instance_id,
                    "provider": "AWS_VM",
                }
                return brownfield_vm(**kwargs)

        class Azure:
            def __new__(cls, instance_name, ip_address=[], instance_id=None):
                kwargs = {
                    "instance_name": instance_name,
                    "address": ip_address,
                    "instance_id": instance_id,
                    "provider": "AZURE_VM",
                }
                return brownfield_vm(**kwargs)

        class Gcp:
            def __new__(cls, instance_name, ip_address=[], instance_id=None):
                kwargs = {
                    "instance_name": instance_name,
                    "address": ip_address,
                    "instance_id": instance_id,
                    "provider": "GCP_VM",
                }
                return brownfield_vm(**kwargs)

        class Vmware:
            def __new__(cls, instance_name, ip_address=[], instance_id=None):
                kwargs = {
                    "instance_name": instance_name,
                    "address": ip_address,
                    "instance_id": instance_id,
                    "provider": "VMWARE_VM",
                }
                return brownfield_vm(**kwargs)
