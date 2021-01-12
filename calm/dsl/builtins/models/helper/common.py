import sys
from ..metadata_payload import get_metadata_obj
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


def get_profile_environment(cls):
    """
    for the given cls, traverse parent reference upto BlueprintType, then traverse down to locate the corresponding
     app-profile class and get the environment linked to the app-profile
    """
    environment = {}
    environment_pc_accounts = {}
    cls_substrate = _walk_to_parent_with_given_type(cls, "SubstrateType")
    if not cls_substrate:
        return environment, environment_pc_accounts

    cls_bp = _walk_to_parent_with_given_type(cls_substrate, "BlueprintType")

    if not cls_bp or not cls_bp.profiles:
        return environment, environment_pc_accounts

    for cls_profile in cls_bp.profiles:
        for cls_deployment in cls_profile.deployments:
            if cls_deployment.substrate.name != str(cls_substrate):
                continue

            environment = getattr(cls_profile, "environment", {})
            if environment:
                LOG.debug(
                    "Found environment {} associated to app-profile {}".format(
                        environment.get("name"), cls_profile
                    )
                )
            else:
                LOG.debug(
                    "No environment associated to the app-profile {}".format(
                        cls_profile
                    )
                )
            break

    if environment:
        environment_cache_data = Cache.get_entity_data_using_uuid(
            entity_type=CACHE.ENTITY.ENVIRONMENT, uuid=environment["uuid"]
        )
        if not environment_cache_data:
            LOG.error(
                "Environment {} not found. Please run: calm update cache".format(
                    environment["name"]
                )
            )
            sys.exit(-1)

        accounts = environment_cache_data.get("accounts_data", {}).get("nutanix_pc", [])
        for acc in accounts:
            environment_pc_accounts[acc["uuid"]] = acc.get("subnet_uuids", [])

    return environment, environment_pc_accounts


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

    project_pc_accounts = {}
    for acc in project_pc_accounts:
        project_pc_accounts[acc] = []
    for acc, subnet_uuids in project_cache_data.get("whitelisted_subnets", {}).items():
        project_pc_accounts[acc] = subnet_uuids

    return (
        dict(uuid=project_cache_data.get("uuid", ""), name=project_name),
        project_pc_accounts,
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


def get_pc_account(cls, environment, project, environment_whitelist, project_whitelist):
    """get PC account, fallback in this order: Substrate class -> environment -> project"""
    if environment and not environment_whitelist:
        LOG.error(
            "Environment {} has no Nutanix PC account.".format(
                environment.get("name", "")
            )
        )
        sys.exit(-1)
    elif not project_whitelist:
        LOG.error(
            "Project {} has no Nutanix PC account.".format(project.get("name", ""))
        )
        sys.exit(-1)

    pc_account_uuid = ""

    # if Substrate has account, use that
    cls_substrate = _walk_to_parent_with_given_type(cls, "SubstrateType")
    if cls_substrate:
        pc_account_uuid = getattr(cls_substrate, "account", {}).get("uuid")

    if not pc_account_uuid:

        # if there is an environment linked use account from environment
        if environment:
            pc_account_uuid = next(iter(environment_whitelist))
        else:

            # use account from project
            pc_account_uuid = next(iter(project_whitelist))

    account_cache_data = Cache.get_entity_data_using_uuid(
        entity_type=CACHE.ENTITY.ACCOUNT, uuid=pc_account_uuid
    )
    if not account_cache_data:
        LOG.error(
            "Nutanix PC account (uuid={}) not found. Please update cache.".format(
                pc_account_uuid
            )
        )
        sys.exit(-1)
    return account_cache_data
