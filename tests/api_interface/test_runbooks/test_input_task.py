import pytest
import uuid

from calm.dsl.cli.main import get_api_client
from calm.dsl.cli.constants import RUNLOG
from tests.sample_runbooks import DslInputRunbook
from utils import upload_runbook, poll_runlog_status, read_test_config


class TestRunbooks:
    @pytest.mark.slow
    @pytest.mark.runbook
    @pytest.mark.parametrize("Runbook", [DslInputRunbook])
    def test_input_task_in_runbook(self, Runbook):
        """ test_input_task """

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

        # polling till runbook run gets to input state
        state, reasons = poll_runlog_status(client, runlog_uuid, [RUNLOG.STATUS.INPUT])

        print(">> Runbook Run state: {}\n{}".format(state, reasons))
        assert state == RUNLOG.STATUS.INPUT

        # getting the input payload from the json
        data = read_test_config()
        input_payload = data[Runbook.action_name]['input_payload']
        expected_output = data[Runbook.action_name]['expected_output']

        # Finding the task_uuid for the input task
        res, err = client.runbook.list_runlogs(runlog_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        response = res.json()
        entities = response["entities"]
        for entity in entities:
            if entity["status"]["type"] == "task_runlog" and entity["status"]["task_reference"]["name"] == "Input_Task":
                input_task = entity["metadata"]["uuid"]

        # calling resume on the input_data on the input task
        res, err = client.runbook.resume(runlog_uuid, input_task, {"properties": input_payload})
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        # polling till runbook run gets to terminal state
        state, reasons = poll_runlog_status(client, runlog_uuid, RUNLOG.TERMINAL_STATES)

        # Finding the task_uuid for the exec task
        res, err = client.runbook.list_runlogs(runlog_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        response = res.json()
        entities = response["entities"]
        for entity in entities:
            if entity["status"]["type"] == "task_runlog" and entity["status"]["task_reference"]["name"] == "Exec_Task":
                exec_task = entity["metadata"]["uuid"]

        print(">> Runbook Run state: {}\n{}".format(state, reasons))
        assert state == RUNLOG.STATUS.SUCCESS

        # Now checking the output of exec task
        print("runlog_id: {}".format(runlog_uuid))
        res, err = client.runbook.runlog_output(runlog_uuid, exec_task)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        runlog_output = res.json()
        output_list = runlog_output['status']['output_list']
        assert output_list[0]['output'] == expected_output

        # delete the runbook
        res, err = client.runbook.delete(rb_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        else:
            print("runbook {} deleted".format(rb_name))
