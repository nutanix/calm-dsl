import time
import pytest
import uuid

from calm.dsl.cli.main import get_api_client
from calm.dsl.cli.constants import RUNLOG
from tests.sample_runbooks import DslSimpleRunbook
from utils import upload_runbook, poll_runlog_status


class TestRunbooks:
    @pytest.mark.runbook
    @pytest.mark.ces
    @pytest.mark.regression
    @pytest.mark.parametrize("Runbook", [DslSimpleRunbook])
    def test_rb_pause_and_play(self, Runbook):
        """ test_pause_and_play """

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

        # polling till runbook run gets to running state
        state, reasons = poll_runlog_status(
            client, runlog_uuid, [RUNLOG.STATUS.RUNNING]
        )

        print(">> Runbook Run state: {}\n{}".format(state, reasons))
        assert state == RUNLOG.STATUS.RUNNING

        # calling pause on the runbook
        _, err = client.runbook.pause(runlog_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        # polling till runbook run gets to paused state
        state, reasons = poll_runlog_status(client, runlog_uuid, [RUNLOG.STATUS.PAUSED])

        print(">> Runbook Run state: {}\n{}".format(state, reasons))
        assert state == RUNLOG.STATUS.PAUSED

        time.sleep(20)

        # calling play on the runbook
        _, err = client.runbook.play(runlog_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        # polling till runbook run gets to terminal state
        state, reasons = poll_runlog_status(client, runlog_uuid, RUNLOG.TERMINAL_STATES)

        print(">> Runbook Run state: {}\n{}".format(state, reasons))
        assert state == RUNLOG.STATUS.SUCCESS

        # delete the runbook
        _, err = client.runbook.delete(rb_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        else:
            print("runbook {} deleted".format(rb_name))
