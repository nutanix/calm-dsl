import pytest
import uuid

from calm.dsl.cli.main import get_api_client
from calm.dsl.cli.constants import RUNLOG
from tests.sample_runbooks import DslConfirmRunbook
from utils import upload_runbook, poll_runlog_status


class TestRunbooks:
    @pytest.mark.slow
    @pytest.mark.runbook
    @pytest.mark.parametrize("Runbook", [DslConfirmRunbook])
    @pytest.mark.parametrize("Helper", [("SUCCESS", [RUNLOG.STATUS.SUCCESS]), ("FAILURE", RUNLOG.FAILURE_STATES)])
    def test_rb_confirm(self, Runbook, Helper):

        client = get_api_client()
        rb_name = "test_runbook_" + str(uuid.uuid4())[-10:]

        rb = upload_runbook(client, rb_name, Runbook)
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

        # polling till runbook run gets to confirm state
        state, reasons = poll_runlog_status(client, runlog_uuid, [RUNLOG.STATUS.CONFIRM])

        print(">> Runbook Run state: {}\n{}".format(state, reasons))
        assert state == RUNLOG.STATUS.CONFIRM

        # Finding the task_uuid for the confirm task
        res, err = client.runbook.list_runlogs(runlog_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        response = res.json()
        entities = response["entities"]
        for entity in entities:
            if entity["status"]["type"] == "task_runlog" and entity["status"]["state"] == RUNLOG.STATUS.CONFIRM:
                task_uuid = entity["metadata"]["uuid"]
                break

        # calling resume on the confirm task with failure state
        res, err = client.runbook.resume(runlog_uuid, task_uuid, {"confirm_answer": Helper[0]})
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        # polling till runbook run gets to terminal state
        state, reasons = poll_runlog_status(client, runlog_uuid, RUNLOG.TERMINAL_STATES)

        print(">> Runbook Run state: {}\n{}".format(state, reasons))
        assert state in Helper[1]

        # delete the runbook
        _, err = client.runbook.delete(rb_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        else:
            print("runbook {} deleted".format(rb_name))
