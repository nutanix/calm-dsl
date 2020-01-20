import pytest
import uuid

from calm.dsl.cli.main import get_api_client
from calm.dsl.cli.constants import RUNLOG
from tests.api_interface.test_runbooks.test_files.http_task import HTTPTask
from utils import upload_runbook, poll_runlog_status


class TestHTTPTasks:
    @pytest.mark.slow
    def test_http_task(self):

        client = get_api_client()
        rb_name = "test_httptask_" + str(uuid.uuid4())[-10:]

        rb = upload_runbook(client, rb_name, HTTPTask)
        rb_state = rb["status"]["state"]
        rb_uuid = rb["metadata"]["uuid"]
        print(">> Runbook state: {}".format(rb_state))
        assert rb_state == "ACTIVE"
        assert rb_name == rb["spec"]["name"]
        assert rb_name == rb["metadata"]["name"]

        # running the runbook
        print("\n>>Running the runbook")

        res, err = client.runbook.run(rb_uuid, {})
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        response = res.json()
        runlog_uuid = response["status"]["runlog_uuid"]

        # polling till runbook run gets to terminal state
        state, reasons = poll_runlog_status(client, runlog_uuid, RUNLOG.TERMINAL_STATES)

        print(">> Runbook Run state: {}\n{}".format(state, reasons))
        assert state == RUNLOG.STATUS.SUCCESS

        # Finding the task_uuid for the exec task
        res, err = client.runbook.list_runlogs(runlog_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        response = res.json()
        entities = response["entities"]
        for entity in entities:
            if entity["status"]["type"] == "task_runlog" and entity["status"]["task_reference"]["name"] == "ExecTask":
                exec_task = entity["metadata"]["uuid"]

        # Now checking the output of exec task
        res, err = client.runbook.runlog_output(runlog_uuid, exec_task)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        runlog_output = res.json()
        output_list = runlog_output['status']['output_list']
        assert output_list[0]['output'] == 'HTTP\n'

        # delete the runbook
        _, err = client.runbook.delete(rb_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        else:
            print("runbook {} deleted".format(rb_name))
