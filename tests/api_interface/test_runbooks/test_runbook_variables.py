import pytest
import uuid

from calm.dsl.cli.main import get_api_client
from calm.dsl.cli.constants import RUNLOG
from tests.sample_runbooks import DslRunbookWithVariables
from utils import upload_runbook, poll_runlog_status, read_test_config


class TestRunbooks:
    @pytest.mark.runbook
    @pytest.mark.regression
    @pytest.mark.parametrize("Runbook", [DslRunbookWithVariables])
    def test_variables_in_runbook(self, Runbook):
        """ test_runbook_variables """

        client = get_api_client()
        rb_name = "test_runbook_" + str(uuid.uuid4())[-10:]

        rb = upload_runbook(client, rb_name, Runbook)
        rb_state = rb["status"]["state"]
        rb_uuid = rb["metadata"]["uuid"]
        print(">> Runbook state: {}".format(rb_state))
        assert rb_state == "ACTIVE"
        assert rb_name == rb["spec"]["name"]
        assert rb_name == rb["metadata"]["name"]

        # getting the run payload from the json
        data = read_test_config()
        run_payload = data[Runbook.action_name]["run_payload"]
        expected_output = data[Runbook.action_name]["expected_output"]

        # running the runbook
        print("\n>>Running the runbook")

        res, err = client.runbook.run(rb_uuid, run_payload)
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
            if (
                entity["status"]["type"] == "task_runlog"
                and entity["status"]["task_reference"]["name"] == "Exec_Task"
            ):
                exec_task = entity["metadata"]["uuid"]

        # Now checking the output of exec task
        print("runlog_id: {}".format(runlog_uuid))
        res, err = client.runbook.runlog_output(runlog_uuid, exec_task)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        runlog_output = res.json()
        output_list = runlog_output["status"]["output_list"]
        assert output_list[0]["output"] == expected_output

        # delete the runbook
        res, err = client.runbook.delete(rb_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        else:
            print("runbook {} deleted".format(rb_name))
