import pytest
import uuid

from calm.dsl.cli.main import get_api_client
from calm.dsl.cli.constants import RUNLOG
from tests.api_interface.test_runbooks.test_files.parallel_task import ParallelTask
from utils import upload_runbook, poll_runlog_status


class TestParallelTasks:
    @pytest.mark.runbook
    @pytest.mark.regression
    def test_parallel_task(self):
        """ test_parallel_tasks """

        client = get_api_client()
        rb_name = "test_paralleltasks_" + str(uuid.uuid4())[-10:]

        rb = upload_runbook(client, rb_name, ParallelTask)
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

        # Check start/end time for child task runlogs to check if tasks run in parallel
        timestamps = {"Delay1": {}, "Delay2": {}, "Delay3": {}}
        res, err = client.runbook.list_runlogs(runlog_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        response = res.json()
        entities = response["entities"]
        for entity in entities:
            if entity["status"]["type"] == "task_runlog":
                task_name = entity["status"]["task_reference"]["name"]
                if timestamps.get(task_name, None) is not None:
                    timestamps[task_name]["start"] = entity["metadata"]["creation_time"]
                    timestamps[task_name]["end"] = entity["metadata"]["last_update_time"]

        if (timestamps["Delay1"]["start"] > timestamps["Delay2"]["end"] or timestamps["Delay1"]["start"] > timestamps["Delay3"]["end"]):
            pytest.fail("Delay1 task started for Delay2 and Delay3 execution")

        if (timestamps["Delay2"]["start"] > timestamps["Delay3"]["end"] or timestamps["Delay2"]["start"] > timestamps["Delay1"]["end"]):
            pytest.fail("Delay2 task started for Delay3 and Delay1 execution")

        if (timestamps["Delay3"]["start"] > timestamps["Delay1"]["end"] or timestamps["Delay3"]["start"] > timestamps["Delay2"]["end"]):
            pytest.fail("Delay3 task started for Delay1 and Delay2 execution")

        # delete the runbook
        _, err = client.runbook.delete(rb_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        else:
            print("runbook {} deleted".format(rb_name))
