import uuid
import copy

from calm.dsl.log import get_logging_handle
from calm.dsl.constants import QUOTA

LOG = get_logging_handle(__name__)


def generate_quota_filter(quota_entities):
    """
    This routine generates filter for quota
    Args:
        quota_entities(dict): Contains quota entity (account, cluster and project)
    Returns:
        _filter(str): quota filter
    """
    # _filter: "account==account; cluster==cluster; project==project;"
    _filter = ""

    quota_entity = [QUOTA.ENTITY.ACCOUNT, QUOTA.ENTITY.CLUSTER, QUOTA.ENTITY.PROJECT]

    for entity_name, entity_val in quota_entities.items():
        if entity_name in quota_entity:
            _filter = _filter + str(entity_name) + "==" + str(entity_val) + ";"

    return _filter


def generate_quota_entity_spec(quota_entities):
    """
    This routine generates quota entity spec
    Args:
        quota_entities(dict): Contains quota entities (account, cluster and project)
    Returns:
        spec(dict): quota entity spec {"account": account_uuid, "cluster": cluster_uuid}
    """
    quota_entity = [QUOTA.ENTITY.ACCOUNT, QUOTA.ENTITY.CLUSTER, QUOTA.ENTITY.PROJECT]

    spec = dict(filter(lambda ele: ele[0] in quota_entity, quota_entities.items()))

    return spec


def generate_quota_state_spec(state, quota_entities):
    """
    This routine generates spec for quota state
    Args:
        quota_entities(dict): Contains quota entity
    Returns:
        (dict): spec of quota state
    """
    return {
        "spec": {
            "resources": {
                "entities": generate_quota_entity_spec(quota_entities=quota_entities),
                "state": state,
            }
        },
        "metadata": {"kind": "quota"},
    }


def _set_quota_state(client, state, quota_entities):
    """
    This routine sets quota state at account, project and default level whichever is provided in quota_entites
    Args:
        states(str): Contains state
        quota_entities(dict): Contains quota entities
    Returns:
        response(dict): response of set quota state API
    """
    spec = generate_quota_state_spec(state=state, quota_entities=quota_entities)

    LOG.info("Spec sent for set quota state: {}".format(spec))

    try:
        res, err = client.quotas.update_state(payload=spec)
        res = res.json()
        LOG.info("Response from function call {}".format(res))

        if (
            isinstance(res, dict)
            and res.get("status", {}).get("state") == "SUCCESS"
            and res.get("status", {}).get("resources", {}).get("state") == state
        ):
            return res, None
        else:
            LOG.error("Quota set state API got failed: {}".format(res))
            return None, "Quota set state API got failed: {}".format(res)
    except Exception as exception:
        LOG.error("Quota set state API raised exception {0}".format(exception))
        return None, exception


def generate_get_quota_spec(quota_entities):
    """
    This routine generates spec for get quota
    Args:
        quota_entities(dict): Contains quota entity (account, cluster and project)
    Returns:
        (dict): spec of get quota
    """
    return {
        "length": 100,
        "offset": 0,
        "filter": generate_quota_filter(quota_entities),
    }


def _get_quota(client, quota_entities):
    """
    This routine returns quota at cluster, project and default level
    Args:
        quota_entities(dict): Contains quota entities
    Returns:
        response(dict): response of get quota API
    """
    spec = generate_get_quota_spec(quota_entities=quota_entities)

    LOG.info("Spec sent for get quota: {}".format(spec))

    try:
        res, err = client.quotas.list(payload=spec)
        res = res.json()
        LOG.info("Response from function call {}".format(res))

        if isinstance(res, dict):
            return res, None
        else:
            LOG.error("Quota get API got failed {0}".format(res))
            return None, "Get quota failed: {0}".format(res)

    except Exception as exception:
        LOG.error("Quota get API raised exception {0}".format(exception))
        return None, exception


def _get_quota_uuid(res):
    """
    This routine returns quota uuid at cluster, project and default level
    Args:
        res(dict): Contains response for getting quota uuid
    Returns:
        quota_uuid(str): Quota uuid
    """
    quota_uuid = None
    if res and res.get("entities") and len(res["entities"]):
        quota_uuid = (
            res["entities"][0].get("status", {}).get("resources", {}).get("uuid")
        )

    LOG.info("Quota Uuid {} ".format(quota_uuid))

    if quota_uuid:
        return quota_uuid, None
    else:
        LOG.info("Quota is not set: {0}".format(res))
        return None, "Quota is not set: {0}".format(res)


def get_quota_uuid_at_project(client, quota_entities):
    """
    This routine returns quota uuid at project level
    Args:
        quota_entities(dict): Contains quota entity (project)
    Returns:
        (str): Quota uuid
    """

    res, err = _get_quota(client=client, quota_entities=quota_entities)

    if res:
        return _get_quota_uuid(res)
    else:
        return None, err


def generate_quota_data_spec(quota):
    """
    This routine generates quota data spec
    Args:
        quota(dict): Contains quota data (memory, disk and vcpu)
    Returns:
        (dict): quota data spec
    """

    data = {"vcpu": -1, "disk": -1, "memory": -1}

    for resource in quota["resources"]:
        if resource["resource_type"] == "VCPUS":
            data["vcpu"] = resource["limit"]
        if resource["resource_type"] == "STORAGE":
            data["disk"] = resource["limit"]
        if resource["resource_type"] == "MEMORY":
            data["memory"] = resource["limit"]

    return data


def generate_create_quota_spec(quota, quota_uuid, quota_entities, project_uuid=None):
    """
    This routine generates spec for create quota
    Args:
        quota(dict): Contains quota data
        quota_uuid(str): Contains quota uuid
        quota_entities(dict): Contains quota entities
        project_uuid(str): Contains project uuid
    Returns:
        spec(dict): spec for create quota
    """

    spec = {
        "metadata": {"uuid": quota_uuid, "kind": "quota"},
        "spec": {
            "resources": {
                "data": generate_quota_data_spec(quota=quota),
                "entities": generate_quota_entity_spec(quota_entities=quota_entities),
                "uuid": quota_uuid,
                "metadata": {},
            }
        },
    }
    if project_uuid:
        spec["metadata"].update(
            {"project_reference": {"kind": "project", "uuid": project_uuid}}
        )

    return spec


def _create_quota(client, quota, project_uuid, quota_entities, quota_uuid=None):
    """
    This routine creates quota
    Args:
        quota(dict): Contains quota data
        project_uuid(str): Contains project uuid
        quota_entities(dict): Contains quota entities
        quota_uuid(str): Contains quota uuid
    Returns:
        response(dict): response of create quota API
    """

    if quota_uuid is None:
        quota_uuid = str(uuid.uuid4())

    spec = generate_create_quota_spec(
        quota=quota,
        project_uuid=project_uuid,
        quota_uuid=quota_uuid,
        quota_entities=quota_entities,
    )

    try:
        LOG.info("Spec sent for creating quota: {}".format(spec))

        res, err = client.quotas.create(payload=spec)
        res = res.json()
        LOG.info("Response from function call {}".format(res))

        if isinstance(res, dict) and res.get("status", {}).get("state") == "SUCCESS":
            return res, None
        else:
            LOG.error("Quota create API got failed {0}".format(res))
            return None, "Quota creation failed: {0}".format(res)

    except Exception as exception:
        LOG.error("Quota create API raised exception {0}".format(exception))
        return None, exception


def create_quota_at_project(client, quota, project_uuid, quota_entities):
    """
    This routine creates quota at project level
    Args:
        quota(dict): Contains quota data
        project_uuid(str): Contains project uuid
        quota_uuid(str): Contains quota uuid
        quota_entities(dict): Contains quota entities
    Returns:
        response(dict): response of create quota API
    """
    entity = {QUOTA.ENTITY.ACCOUNT, QUOTA.ENTITY.CLUSTER}

    if (
        entity.intersection(quota_entities.keys())
        or QUOTA.ENTITY.PROJECT not in quota_entities
    ):
        LOG.error(
            "Quota entity is not correct in create quota at project: {0}".format(
                quota_entities
            )
        )
        return None, "Quota entity is not correct: {0}".format(quota_entities)

    return _create_quota(
        client, quota=quota, project_uuid=project_uuid, quota_entities=quota_entities
    )


def generate_set_quota_spec(quota, project_uuid, quota_uuid, quota_entities):
    """
    This routine generates spec for set quota
    Args:
        quota(dict): Contains quota data
        project_uuid(str): Contains project uuid
        quota_uuid(str): Contains quota uuid
        quota_entities(dict): Contains quota entities
    Returns:
        update_spec(dict): spec of set quota
    """
    update_spec = copy.deepcopy(
        generate_create_quota_spec(
            quota=quota,
            project_uuid=project_uuid,
            quota_uuid=quota_uuid,
            quota_entities=quota_entities,
        )
    )

    spec = {
        "spec": {
            "resources": {
                "entity_type": "vm",
                "metadata": {},
                "state": QUOTA.STATE.ENABLED,
            }
        }
    }
    update_spec["spec"]["resources"].update(spec["spec"]["resources"])
    return update_spec


def _set_quota(client, quota, project_uuid, quota_uuid, quota_entities):
    """
    This routine sets quota at cluster, project and default level
    Args:
        quota(dict): Contains quota data
        project_uuid(str): Contains project uuid
        quota_uuid(str): Contains quota uuid
        quota_entities(dict): Contains quota entities
    Returns:
        response(dict): response of set quota API
    """
    spec = generate_set_quota_spec(
        quota=quota,
        project_uuid=project_uuid,
        quota_uuid=quota_uuid,
        quota_entities=quota_entities,
    )
    try:
        LOG.info("Spec sent for set quota: {}".format(spec))

        res, err = client.quotas.update(payload=spec, quota_uuid=quota_uuid)

        LOG.info("Response from function call {}".format(res))

        if not err:
            return res, None
        else:
            LOG.error("Quota set API got failed {0}".format(res))
            return None, "Quota set API got failed {0}".format(res)

    except Exception as exception:
        return None, exception


def set_quota_at_project(client, quota, project_uuid, quota_uuid, quota_entities):
    """
    This routine sets quota at project level
    Args:
        quota(dict): Contains quota data
        project_uuid(str): Contains project uuid
        quota_uuid(str): Contains quota uuid
        quota_entities(dict): Contains quota entities
    Returns:
        (dict): response of set quota API
    """
    entity = {QUOTA.ENTITY.ACCOUNT, QUOTA.ENTITY.CLUSTER}

    if (
        entity.intersection(quota_entities.keys())
        or QUOTA.ENTITY.PROJECT not in quota_entities
    ):
        LOG.error(
            "Quota entity is not correct in set quota at project: {0}".format(
                quota_entities
            )
        )
        return None, "Quota entity is not correct in set quota at project: {0}".format(
            quota_entities
        )

    return _set_quota(
        client=client,
        quota_uuid=quota_uuid,
        project_uuid=project_uuid,
        quota=quota,
        quota_entities=quota_entities,
    )
