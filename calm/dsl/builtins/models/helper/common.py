import sys
import json
from ..metadata_payload import get_metadata_obj
from calm.dsl.api import get_api_client
from calm.dsl.store import Cache
from calm.dsl.config import get_context
from calm.dsl.log import get_logging_handle
from calm.dsl.constants import CACHE

LOG = get_logging_handle(__name__)


def _walk_to_parent_with_given_type(cls, parent_type):
    """traverse parent reference for the given class until reach a class that matches the given type"""
    try:
        if cls.__class__.__name__ == parent_type:
            return cls

        return _walk_to_parent_with_given_type(cls.__parent__, parent_type)
    except (AttributeError, TypeError):
        LOG.debug("cls {} has no parent reference".format(cls))
        return None


def get_project_with_pc_account():
    """get project from metadata/config along with whitelisted accounts and subnets"""

    project_cache_data = get_cur_context_project()
    project_name = project_cache_data["name"]
    project_pc_accounts = project_cache_data.get("accounts_data", {}).get(
        "nutanix_pc", []
    )
    if not project_pc_accounts:
        LOG.error("No nutanix account registered to project {}".format(project_name))
        sys.exit(-1)

    accounts_data = {}
    for ntnx_acc_uuid in project_pc_accounts:
        accounts_data[ntnx_acc_uuid] = {
            "subnet_uuids": project_cache_data["whitelisted_subnets"].get(ntnx_acc_uuid)
            or [],
            "vpc_uuids": project_cache_data["whitelisted_vpcs"].get(ntnx_acc_uuid)
            or [],
            "cluster_uuids": project_cache_data["whitelisted_clusters"].get(
                ntnx_acc_uuid
            )
            or [],
        }

    return (
        dict(uuid=project_cache_data.get("uuid", ""), name=project_name),
        accounts_data,
    )


def get_cur_context_project():
    """
    Returns project in current context i.e. from metadata/config
    fallback in this order: metadata(defined in dsl file) -> config
    """
    metadata_obj = get_metadata_obj()
    project_ref = metadata_obj.get("project_reference") or dict()

    # If project not found in metadata, it will take project from config
    context = get_context()
    project_config = context.get_project_config()
    project_name = project_ref.get("name") or project_config["name"]

    project_cache_data = Cache.get_entity_data(
        entity_type=CACHE.ENTITY.PROJECT, name=project_name
    )
    if not project_cache_data:
        LOG.error(
            "Project {} not found. Please run: calm update cache".format(project_name)
        )
        sys.exit(-1)

    return project_cache_data


def get_project(name=None, project_uuid=""):

    if not (name or project_uuid):
        LOG.error("One of name or uuid must be provided")
        sys.exit(-1)

    client = get_api_client()
    if not project_uuid:
        params = {"filter": "name=={}".format(name)}

        LOG.info("Searching for the project {}".format(name))
        res, err = client.project.list(params=params)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        response = res.json()
        entities = response.get("entities", None)
        project = None
        if entities:
            if len(entities) != 1:
                raise Exception("More than one project found - {}".format(entities))

            LOG.info("Project {} found ".format(name))
            project = entities[0]
        else:
            raise Exception("No project found with name {} found".format(name))

        project_uuid = project["metadata"]["uuid"]
        LOG.info("Fetching details of project {}".format(name))

    else:
        LOG.info("Fetching details of project (uuid='{}')".format(project_uuid))

    res, err = client.project.read(project_uuid)  # for getting additional fields
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    project = res.json()
    return project


def get_vmware_account_from_datacenter(datacenter="Sabine59-DC"):
    """
    Returns the datacenter attached to given datacenter.
    Default datacenter = Sabine59-DC
    """

    client = get_api_client()
    res, err = client.account.list(params={"filter": "type==vmware;state==VERIFIED"})
    if err:
        LOG.error(err)
        sys.exit(-1)

    res = res.json()
    vmw_account_name = ""
    for entity in res["entities"]:
        if entity["status"]["resources"]["data"].get("datacenter", "") == datacenter:
            vmw_account_name = entity["status"]["name"]

    return vmw_account_name


def is_macro(var):
    """returns true if given var is macro"""
    return var.startswith("@@{") and var.endswith("}@@")


def get_pe_account_uuid_using_pc_account_uuid_and_subnet_uuid(
    pc_account_uuid, subnet_uuid
):
    """
    returns pe account uuid using pc account uuid and subnet_uuid
    """

    subnet_cache_data = Cache.get_entity_data_using_uuid(
        entity_type=CACHE.ENTITY.AHV_SUBNET,
        uuid=subnet_uuid,
        account_uuid=pc_account_uuid,
    )
    if not subnet_cache_data:
        LOG.error(
            "AHV Subnet (uuid='{}') not found. Please check subnet or update cache".format(
                subnet_uuid
            )
        )
        sys.exit("Ahv Subnet {} not found".format(subnet_uuid))

    # As for nutanix accounts, cluster name is account name
    LOG.debug("Subnet cache data: {}".format(subnet_cache_data))
    subnet_cluster_name = subnet_cache_data["cluster_name"]

    pc_account_cache = Cache.get_entity_data_using_uuid(
        entity_type=CACHE.ENTITY.ACCOUNT, uuid=pc_account_uuid
    )
    pc_clusters = pc_account_cache["data"].get("clusters", {})
    pc_clusters_rev = {v: k for k, v in pc_clusters.items()}

    return pc_clusters_rev.get(subnet_cluster_name, "")


def get_pe_account_uuid_using_pc_account_uuid_and_nic_data(
    pc_account_uuid, subnet_name, cluster_name
):
    """
    returns pe account uuid using pc account uuid and subnet_name and cluster_name
    """

    subnet_cache_data = Cache.get_entity_data(
        entity_type=CACHE.ENTITY.AHV_SUBNET,
        name=subnet_name,
        cluster=cluster_name,
        account_uuid=pc_account_uuid,
    )

    if not subnet_cache_data:
        LOG.error(
            "Ahv Subnet (name = '{}') not found in registered Nutanix PC account (uuid = '{}') ".format(
                subnet_name, pc_account_uuid
            )
        )
        sys.exit("AHV Subnet {} not found".format(subnet_name))

    # As for nutanix accounts, cluster name is account name
    subnet_cluster_name = subnet_cache_data["cluster_name"]

    pc_account_cache = Cache.get_entity_data_using_uuid(
        entity_type=CACHE.ENTITY.ACCOUNT, uuid=pc_account_uuid
    )
    pc_clusters = pc_account_cache["data"].get("clusters", {})
    pc_clusters_rev = {v: k for k, v in pc_clusters.items()}

    return pc_clusters_rev.get(subnet_cluster_name, "")


def get_pe_account_using_pc_account_uuid_and_cluster_name(
    pc_account_uuid, cluster_name
):
    """
    returns pe account uuid using pc account uuid and cluster_name
    """
    cluster_cache_data = Cache.get_entity_data(
        entity_type=CACHE.ENTITY.AHV_CLUSTER,
        name=cluster_name,
        account_uuid=pc_account_uuid,
    )
    return cluster_cache_data.get("pe_account_uuid", "")


def get_network_group(name=None, tunnel_uuid=None):

    if not (name):
        LOG.error(" name  must be provided")
        sys.exit(-1)

    nested_attributes = [
        "tunnel_name",
        "tunnel_vm_name",
        "tunnel_status",
        "app_uuid",
        "app_status",
    ]

    client = get_api_client()
    network_group_uuid = None
    network_group = None
    if not network_group_uuid:
        params = {}
        filter_query = ""
        if name:
            params = {"filter": "name=={}".format(name)}
        elif tunnel_uuid:
            params = {"filter": "tunnel_reference=={}".format(tunnel_uuid)}
        params["nested_attributes"] = nested_attributes

        LOG.info("Searching for the network group {}".format(name))
        res, err = client.network_group.list(params=params)
        if err:
            LOG.exception("[{}] - {}".format(err["code"], err["error"]))

        response = res.json()
        entities = response.get("entities", None)
        network_group = None
        if entities:
            if len(entities) != 1:
                LOG.exception("More than one Network Group found - {}".format(entities))

            LOG.info("Network Group {} found ".format(name))
            network_group = entities[0]
        else:
            LOG.exception("No Network Group found with name {} found".format(name))

    return network_group


def get_network_group_by_tunnel_name(name):

    if not (name):
        LOG.error(" name  must be provided")
        sys.exit(-1)

    nested_attributes = [
        "tunnel_name",
        "tunnel_vm_name",
        "tunnel_status",
        "app_uuid",
        "app_status",
    ]

    client = get_api_client()

    network_group = {}

    params = {"filter": "name=={}".format(name)}
    res, err = client.tunnel.list(params=params)
    if err:
        LOG.exception("[{}] - {}".format(err["code"], err["error"]))
    response = res.json()
    LOG.debug("Tunnel response: {}".format(response))

    tunnels = response.get("entities", [])
    if not tunnels:
        LOG.exception("No Tunnel found with name: {}".format(name))

    tunnel_uuid = tunnels[0].get("metadata", {}).get("uuid")

    if tunnel_uuid:
        params = {"filter": "tunnel_reference=={}".format(tunnel_uuid)}
        params["nested_attributes"] = nested_attributes

        LOG.info("Searching for the network group using tunnel name: {}".format(name))
        res, err = client.network_group.list(params=params)
        if err:
            LOG.exception("[{}] - {}".format(err["code"], err["error"]))

        response = res.json()
        entities = response.get("entities", None)
        network_group = None
        if entities:
            if len(entities) != 1:
                LOG.exception("More than one Network Group found - {}".format(entities))

            LOG.info("Network Group {} found ".format(name))
            network_group = entities[0]
        else:
            LOG.exception("No Network Group found with name {} found".format(name))

    return network_group
