import sys
import pytz
from dateutil.parser import parse
from dateutil import tz

from ..metadata_payload import get_metadata_obj
from calm.dsl.api import get_api_client
from calm.dsl.store import Cache
from calm.dsl.config import get_context
from calm.dsl.log import get_logging_handle
from calm.dsl.constants import CACHE
from calm.dsl.db.table_config import ResourceTypeCache

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
    if "@@{" in var:
        return True
    return False


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
    return get_pe_account_using_pc_account_uuid_and_cluster_name(
        pc_account_uuid, subnet_cluster_name
    )


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

    # As for nutanix accounts, cluster name is account name (Needed if cluster_name is not supplied)
    subnet_cluster_name = subnet_cache_data["cluster_name"]
    return get_pe_account_using_pc_account_uuid_and_cluster_name(
        pc_account_uuid, subnet_cluster_name
    )


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


def get_variable_list_and_task_name_for_rt_and_action(
    resource_type_name, action_name, provider_name
):
    """
    Fetch variable list and Plugin Task Name for given RT name and one of it's action name
    Args:
        resource_type_name (str): Name for this Resource Type
        action_name (str): Name of the Resource Type action
        provider_name (str): Name of the provider
    Returns:
        ([dict]): Array of Variable List
        (str): Plugin Task name
    """

    res = get_resource_type(resource_type_name, provider_name)
    action_list = res["action_list"]

    variable_list = []
    task_name = None
    for rt_action in action_list:
        if action_name == rt_action["name"]:
            variable_list = rt_action["runbook"]["variable_list"]
            task_name = rt_action["runbook"]["task_definition_list"][1]["name"]
            break

    return variable_list, task_name


def get_ndb_profile(name, profile_type, account_name, **kwargs):
    """
    Fetch profile wrt name, profile_type account_name and kwargs given
    Args:
        name (str): Name of the profile
        profile_type (str): type of profile
        account_name (str): Name of the account
    Returns:
        (dict): Profile dictionary
    """

    engine = kwargs.get("engine", "")
    if not account_name:
        LOG.error(
            "Account Name is required NutanixDB Profile type {} compile, pls pass Account name".format(
                profile_type
            )
        )
        sys.exit(-1)

    query_obj = {
        "entity_type": CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.PROFILE,
        "name": name,
        "account_name": account_name,
        "type": profile_type,
    }
    if kwargs.get("engine", ""):
        query_obj["engine_type"] = kwargs["engine"]
    cache_profile_data = Cache.get_entity_data(**query_obj)

    if not cache_profile_data:
        LOG.error("No NDB {} Profile with name '{}' found".format(profile_type, name))
        sys.exit(-1)

    return cache_profile_data


def get_ndb_tag(name, account_name, entity_type):
    """
    FetchTag wrt name, account_name and kwargs given
    Args:
        name (str): Name of the tag
        account_name (str): ID of the account
    Returns:
        (dict): Tag dictionary
    """
    cache_tag_data = Cache.get_entity_data(
        entity_type=CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.TAG,
        name=name,
        account_name=account_name,
        type=entity_type,
    )

    if not cache_tag_data:
        LOG.error("No NDB {} Tag with name '{}' found".format(entity_type, name))
        sys.exit("No NDB {} Tag with name '{}' found".format(entity_type, name))

    return cache_tag_data


def get_resource_type(name, provider_name):
    """
    Fetched resource_type
    Args:
        name (str): Name for this Resource Type
        provider_name (str): Name of the provider
    Returns:
        (dict): Resource_type response dict
    """
    resource_type = ResourceTypeCache.get_entity_data(
        name=name, provider_name=provider_name
    )
    if not resource_type:
        LOG.error("No resource_type with name '{}' found".format(name))
        sys.exit("No resource_type with name '{}' found".format(name))
    return resource_type


def macro_or_ref_validation(val, ref, err_msg):
    """Validate if val is either macro or the correct ref"""
    if is_not_macro(val) and is_not_right_ref(val, ref):
        raise ValueError(err_msg)


def is_not_macro(val):
    """Check if val is not a macro"""
    return not (isinstance(val, str) and is_macro(val))


def is_not_right_ref(val, ref):
    """Check if val is not the ref for given reference"""
    return not (getattr(val, "get_ref_cls", None) and val.get_ref_cls() == ref)


def get_timestamp_in_utc(timestamp, from_timezone, time_format="%Y-%m-%d %H:%M:%S"):
    """Convert timeStamp in given timezone to UTC"""
    if from_timezone not in pytz.all_timezones_set:
        raise ValueError(
            "{} is invalid, Please provide valid timezone.\nSupported timezones are {}".format(
                from_timezone, pytz.all_timezones_set
            )
        )
    from_zone = tz.gettz(from_timezone)
    tme = parse(timestamp).replace(tzinfo=from_zone)
    return tme.astimezone(tz.gettz("UTC")).strftime(time_format)


def get_provider_uuid(name):
    """returns provider uuid if present else raises error"""

    client = get_api_client()
    params = {"filter": "name=={}".format(name)}

    res, err = client.provider.list(params=params)
    if err:
        LOG.exception("[{}] - {}".format(err["code"], err["error"]))
        sys.exit("[{}] - {}".format(err["code"], err["error"]))

    response = res.json()
    entities = response.get("entities", None)
    provider = None
    if entities:
        if len(entities) != 1:
            LOG.error("More than one provider found - {}".format(entities))
            sys.exit(-1)

        LOG.info("{} found ".format(name))
        provider = entities[0]
    else:
        LOG.error("No provider found with name {} found".format(name))
        sys.exit("No provider found with name {} found".format(name))

    return provider["metadata"]["uuid"]


def get_provider(name):
    """returns provider get call data"""

    client = get_api_client()
    provider_uuid = get_provider_uuid(name=name)
    res, err = client.provider.read(provider_uuid)
    if err:
        LOG.exception("[{}] - {}".format(err["code"], err["error"]))
        sys.exit("[{}] - {}".format(err["code"], err["error"]))

    return res.json()
