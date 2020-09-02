import pytest
from ruamel import yaml
import uuid

from calm.dsl.cli.main import get_api_client
from calm.dsl.cli.task_commands import watch_task
from calm.dsl.cli.constants import ERGON_TASK
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)
PROJECT_SPEC_FILE_LOCATION = "tests/api_interface/entity_spec/sample_project.json"


class TestProjects:
    def test_projects_list(self):

        client = get_api_client()

        params = {"length": 20, "offset": 0}
        LOG.info("Invoking list api call on projects")
        res, err = client.project.list(params=params)

        if not err:
            assert res.ok is True
            LOG.info("Success")
            LOG.debug("Response: {}".format(res.json()))

        else:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

    def test_projects_crud(self):

        client = get_api_client()
        project_name = "test_proj" + str(uuid.uuid4())[-10:]
        project_payload = yaml.safe_load(open(PROJECT_SPEC_FILE_LOCATION, "r").read())

        project_payload["spec"]["name"] = project_name
        project_payload["metadata"]["name"] = project_name

        # Create API
        LOG.info("Creating project {}".format(project_name))
        res, err = client.project.create(project_payload)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        else:
            assert res.ok is True
            res = res.json()
            assert project_name == res["metadata"]["name"]
            task_state = watch_task(res["status"]["execution_context"]["task_uuid"])
            if task_state in ERGON_TASK.FAILURE_STATES:
                pytest.fail("Project creation task went to {} state".format(task_state))
            LOG.info("Success")
            LOG.debug("Response: {}".format(res))

        # Read API
        project_uuid = res["metadata"]["uuid"]
        LOG.info("Reading project {}".format(project_name))
        res, err = client.project.read(project_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        else:
            assert res.ok is True
            res = res.json()
            assert project_name == res["metadata"]["name"]
            LOG.info("Success")
            LOG.debug("Response: {}".format(res))

        # Update API
        LOG.info("Updating project {}".format(project_name))
        project_upd_des = "Sample project Description {}".format(str(uuid.uuid4()))

        res.pop("status", None)
        project_payload = res
        project_payload["spec"]["description"] = project_upd_des

        res, err = client.project.update(project_uuid, project_payload)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        else:
            assert res.ok is True
            res = res.json()
            assert project_name == res["metadata"]["name"]
            assert project_upd_des == res["spec"]["description"]
            task_state = watch_task(res["status"]["execution_context"]["task_uuid"])
            if task_state in ERGON_TASK.FAILURE_STATES:
                pytest.fail("Project creation task went to {} state".format(task_state))
            LOG.info("Success")
            LOG.debug("Response: {}".format(res))

        # Delete API
        LOG.info("Deleting project {}".format(project_name))
        res, err = client.project.delete(project_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        else:
            assert res.ok is True
            res = res.json()
            task_state = watch_task(res["status"]["execution_context"]["task_uuid"])
            if task_state in ERGON_TASK.FAILURE_STATES:
                pytest.fail("Project deletion task went to {} state".format(task_state))
            LOG.info("Success")
            LOG.debug("Response: {}".format(res))
