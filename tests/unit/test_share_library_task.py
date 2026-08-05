"""
Unit tests for command:
    - calm share library task "Task Name" -p project1 -p project2
    - calm unshare library task "Task Name" -p project1 -p project2


Covered scenarios
-----------------
Combined add + remove in a single test     (via share_task + unshare_task)
"""

from unittest import mock

from calm.dsl.cli.library_tasks import share_task, unshare_task

TASK_UUID = "aaaaaaaa-0000-0000-0000-000000000001"
OWNER_PROJECT = "owner_proj"


def _make_get_task_response(existing_projects=None):
    """Simulates the object returned by get_task() (list-API entity)."""
    return {
        "metadata": {"uuid": TASK_UUID},
        "status": {
            "resources": {
                "project_reference_list": existing_projects or [],
            }
        },
    }


def _make_task_data(existing_projects=None, owner=OWNER_PROJECT):
    """Simulates the object returned by client.task.read().json() (GET entity)."""
    return {
        "api_version": "3.0",
        "metadata": {
            "kind": "app_task",
            "uuid": TASK_UUID,
            "name": "My Task",
            "spec_version": 1,
            "last_update_time": "1780993829437697",
            "creation_time": "1780993829437697",
            "owner_reference": {"kind": "user", "name": "admin", "uuid": "00000000"},
            "project_reference": {"kind": "project", "name": owner, "uuid": "p-uuid"},
        },
        "spec": {
            "name": "My Task",
            "description": "",
            "resources": {
                "type": "EXEC",
                "attrs": {"script_type": "sh", "script": "ls"},
                "variable_list": [],
                "project_reference_list": existing_projects or [],
            },
        },
        "status": {
            "resources": {
                "project_reference_list": existing_projects or [],
            }
        },
    }


def _proj_ref(name):
    return {"kind": "project", "name": name, "uuid": "uuid-" + name}


def setup_client_mock(client_mock, task_data):
    read_res = mock.MagicMock()
    read_res.json.return_value = task_data
    client_mock.task.read.return_value = (read_res, None)
    client_mock.task.share.return_value = (mock.MagicMock(), None)


@mock.patch("calm.dsl.cli.library_tasks.Ref")
@mock.patch("calm.dsl.cli.library_tasks.get_api_client")
@mock.patch("calm.dsl.cli.library_tasks.get_task")
def test_share_and_unshare_task__combined_add_and_remove(
    mock_get_task, mock_get_client, mock_ref
):
    """share_task adds proj_new; a subsequent unshare_task removes proj_old."""
    existing = [_proj_ref("proj_old"), _proj_ref("proj_keep")]
    task_data = _make_task_data(existing_projects=existing)
    mock_get_task.return_value = _make_get_task_response(existing_projects=existing)
    setup_client_mock(mock_get_client.return_value, task_data)
    mock_ref.Project.side_effect = lambda name: _proj_ref(name)

    # Share adds proj_new
    share_task("My Task", projects=["proj_new"])

    # Refresh task_data to reflect the updated list after share
    updated_existing = existing + [_proj_ref("proj_new")]
    task_data2 = _make_task_data(existing_projects=updated_existing)
    mock_get_task.return_value = _make_get_task_response(
        existing_projects=updated_existing
    )
    setup_client_mock(mock_get_client.return_value, task_data2)

    # Unshare removes proj_old
    unshare_task("My Task", projects=["proj_old"])

    payload = mock_get_client.return_value.task.share.call_args[0][1]
    names = {p["name"] for p in payload["spec"]["resources"]["project_reference_list"]}
    assert "proj_new" in names
    assert "proj_keep" in names
    assert "proj_old" not in names
