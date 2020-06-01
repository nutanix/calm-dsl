import pytest
from ruamel import yaml
import uuid

from calm.dsl.cli.main import get_api_client
from calm.dsl.cli.projects import poll_calm_projects_task
from calm.dsl.tools import get_logging_handle

LOG = get_logging_handle(__name__)


class TestProjects:
    def test_projects_list(self):

        client = get_api_client()

        params = {"length": 20, "offset": 0}
        LOG.info("Invoking list api call on projects")
        res, err = client.blueprint.list(params=params)

        if not err:
            assert res.ok is True
            LOG.info("Success")
            LOG.debug("Response: {}".format(res.json()))

        else:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

    def test_projects_crud(self):

        client = get_api_client()
        file_location = "tests/api_interface/entity_spec/sample_project.json"
        project_payload = yaml.safe_load(open(file_location, "r").read())

        payload = {
            "api_version": "3.0",
            "metadata": {"kind": "project"},
            "spec": project_payload,
        }

        project_name = "test_proj" + str(uuid.uuid4())[-10:]
        payload["spec"]["project_detail"]["name"] = project_name

        LOG.info("Creating project {}".format(project_name))
        res, err = client.project.create(payload)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        else:
            assert res.ok is True
            res = res.json()
            LOG.debug("Response: {}".format(res))
            assert project_name == res["spec"]["project_detail"]["name"]
            project_uuid = res["metadata"]["uuid"]
            task_uuid = res["status"]["execution_context"]["task_uuid"]
            poll_calm_projects_task(project_uuid=project_uuid, task_uuid=task_uuid)

        LOG.info("Reading project {}".format(project_name))
        res, err = client.project.read(project_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        else:
            assert res.ok is True
            res = res.json()
            LOG.info("Success")
            LOG.debug("Response: {}".format(res))

        LOG.info("Updating project {}".format(project_name))
        file_location = "tests/api_interface/entity_spec/sample_project_update.json"
        project_payload = yaml.safe_load(open(file_location, "r").read())
        spec_version = res["metadata"]["spec_version"]

        payload = {
            "api_version": "3.0",
            "metadata": {
                "kind": "project",
                "uuid": project_uuid,
                "spec_version": spec_version,
            },
            "spec": project_payload,
        }

        project_name = "test_proj" + str(uuid.uuid4())[-10:]
        payload["spec"]["project_detail"]["name"] = project_name

        res, err = client.project.update(project_uuid, payload)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        else:
            assert res.ok is True
            res = res.json()
            LOG.debug("Response: {}".format(res))
            assert project_name == res["spec"]["project_detail"]["name"]
            task_uuid = res["status"]["execution_context"]["task_uuid"]
            poll_calm_projects_task(project_uuid=project_uuid, task_uuid=task_uuid)

        LOG.info("Deleting project {}".format(project_name))
        res, err = client.project.delete(project_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        else:
            assert res.ok is True
            res = res.json()
            LOG.debug("Response: {}".format(res))
            task_uuid = res["status"]["execution_context"]["task_uuid"]
            poll_calm_projects_task(project_uuid=project_uuid, task_uuid=task_uuid)
