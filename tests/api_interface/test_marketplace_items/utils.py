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
    res, err = client.market_place.update(uuid=mpi_uuid, payload=mpi_data)

    if err:
        pytest.fail("[{}] - {}".format(err["code"], err["error"]))

    return res.json()
