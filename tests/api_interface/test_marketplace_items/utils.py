import uuid
import pytest
from calm.dsl.cli.constants import MARKETPLACE_ITEM
from calm.dsl.config import get_config


def publish_runbook_to_marketplace_manager(
    client,
    runbook_uuid,
    marketplace_item_name,
    version,
    description="",
    with_secrets=False,
    with_endpoints=False,
    app_group_uuid=None,
    app_icon_uuid=None,
    icon_file=None,
):

    config = get_config()

    mpi_spec = {
        "spec": {
            "name": marketplace_item_name,
            "description": description,
            "resources": {
                "app_attribute_list": ["FEATURED"],
                "icon_reference_list": [],
                "author": config["SERVER"]["pc_username"],
                "version": version,
                "type": MARKETPLACE_ITEM.TYPES.RUNBOOK,
                "app_group_uuid": app_group_uuid or str(uuid.uuid4()),
                "runbook_template_info": {
                    "is_published_with_secrets": with_secrets,
                    "is_published_with_endpoints": with_endpoints,
                    "source_runbook_reference": {
                        "uuid": runbook_uuid,
                        "kind": "runbook",
                    }
                },
            },
        },
        "api_version": "3.0",
        "metadata": {"kind": "marketplace_item"},
    }

    if app_icon_uuid:
        mpi_spec["spec"]["resources"]["icon_reference_list"] = [
            {
                "icon_type": "ICON",
                "icon_reference": {"kind": "file_item", "uuid": app_icon_uuid},
            }
        ]

    res, err = client.market_place.create(mpi_spec)
    if err:
        pytest.fail("[{}] - {}".format(err["code"], err["error"]))

    return res.json()


def change_state(client, mpi_uuid, new_state,
                 project_list=None):
    """change state of MPI and change project sharing list"""

    res, err = client.market_place.read(mpi_uuid)
    if err:
        pytest.fail("[{}] - {}".format(err["code"], err["error"]))

    mpi_data = res.json()
    mpi_data.pop("status", None)
    mpi_data["spec"]["resources"]["app_state"] = new_state
    if project_list is not None:
        project_reference_list = []
        for project in project_list:
            project_params = {"filter": "name=={}".format(project)}
            res, err = client.project.list(params=project_params)
            if err:
                pytest.fail("[{}] - {}".format(err["code"], err["error"]))

            response = res.json()
            entities = response.get("entities", None)
            if not entities:
                raise Exception("No project with name {} exists".format(project))

            project_id = entities[0]["metadata"]["uuid"]
            project_reference_list.append({
                "name": project,
                "uuid": project_id,
                "kind": "project"
            })

        mpi_data['spec']['resources']['project_reference_list'] = project_reference_list

    res, err = client.market_place.update(uuid=mpi_uuid, payload=mpi_data)
    if err:
        pytest.fail("[{}] - {}".format(err["code"], err["error"]))

    return res.json()


def clone_marketplace_runbook(client, mpi_uuid, runbook_name, project):

    project_params = {"filter": "name=={}".format(project)}
    res, err = client.project.list(params=project_params)
    if err:
        pytest.fail("[{}] - {}".format(err["code"], err["error"]))

    response = res.json()
    project_entities = response.get("entities", None)
    if not project_entities:
        raise Exception("No project with name {} exists".format(project))

    project_id = project_entities[0]["metadata"]["uuid"]

    payload = {
        "api_version": "3.0",
        "metadata": {
            "name": runbook_name,
            "project_reference": {
                "name": project,
                "uuid": project_id,
                "kind": "project"
            },
            "kind": "runbook"
        },
        "spec": {
            "name": runbook_name,
            "resources": {
                "marketplace_reference": {
                    "uuid": mpi_uuid,
                    "kind": "marketplace_item"
                }
            }
        }
    }

    res, err = client.runbook.marketplace_clone(payload)
    if err:
        pytest.fail("[{}] - {}".format(err["code"], err["error"]))

    response = res.json()
    return response['runbook_uuid']


def execute_marketplace_runbook(client, mpi_uuid, project_name,
                                default_endpoint_uuid=None,
                                endpoints_mapping=None,
                                runtime_variables=None):

    project_params = {"filter": "name=={}".format(project_name)}
    res, err = client.project.list(params=project_params)
    if err:
        pytest.fail("[{}] - {}".format(err["code"], err["error"]))

    response = res.json()
    project_entities = response.get("entities", None)
    if not project_entities:
        raise Exception("No project with name {} exists".format(project_name))

    project_id = project_entities[0]["metadata"]["uuid"]

    payload = {
        "api_version": "3.0",
        "metadata": {
            "project_reference": {
                "name": project_name,
                "uuid": project_id,
                "kind": "project"
            },
            "kind": "runbook"
        },
        "spec": {
            "resources": {
                "marketplace_reference": {
                    "uuid": mpi_uuid,
                    "kind": "marketplace_item"
                }
            }
        }
    }

    if runtime_variables:
        payload['spec']['resources']['args'] = runtime_variables

    if default_endpoint_uuid:
        payload['spec']['resources']['default_target_reference'] = {
            "uuid": default_endpoint_uuid,
            "kind": "app_endpoint"
        }

    if endpoints_mapping:
        payload['spec']['resources']['endpoints_mapping'] = endpoints_mapping

    res, err = client.runbook.marketplace_execute(payload)
    if err:
        pytest.fail("[{}] - {}".format(err["code"], err["error"]))

    response = res.json()
    return response['status']['runlog_uuid']
