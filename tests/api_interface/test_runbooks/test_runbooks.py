import pytest
import uuid

from calm.dsl.cli.main import get_api_client
from calm.dsl.cli.constants import RUNLOG
from tests.sample_runbooks import DslPausePlayRunbook
from utils import upload_runbook, update_runbook, poll_runlog_status


class TestRunbooks:
    def test_runbooks_list(self):

        client = get_api_client()

        params = {"length": 20, "offset": 0}
        res, err = client.runbook.list(params=params)

        if not err:
            print("\n>> Runbook list call successful>>")
            assert res.ok is True
        else:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

    @pytest.mark.slow
    @pytest.mark.parametrize("Runbook", [DslPausePlayRunbook])
    def test_upload_and_run_rb(self, Runbook):

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

    @pytest.mark.slow
    @pytest.mark.parametrize("Runbook", [DslPausePlayRunbook])
    def test_rb_crud(self, Runbook):

        client = get_api_client()
        rb_name = "test_ask_" + str(uuid.uuid4())[-10:]

        rb = upload_runbook(client, rb_name, Runbook)
        rb_state = rb["status"]["state"]
        rb_uuid = rb["metadata"]["uuid"]
        print(">> Runbook state: {}".format(rb_state))
        assert rb_state == "ACTIVE"
        assert rb_name == rb["spec"]["name"]
        assert rb_name == rb["metadata"]["name"]

        # reading the runbook using get call
        print("\n>>Reading Runbook")
        res, err = client.runbook.read(rb_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        else:
            assert res.ok is True
            res = res.json()
            assert rb_name == res["spec"]["name"]
            assert rb_name == res["metadata"]["name"]
            assert rb_name == res["metadata"]["name"]
            print(">> Get call to runbook is successful >>")

        # deleting runbook
        print("\n>>Deleting runbook")
        res, err = client.runbook.delete(rb_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        else:
            assert res.ok is True
            res = res.json()
            print("API Response: {}".format(res["description"]))
            print(">> Delete call to runbook is successful >>")

    @pytest.mark.skip(reason="runbook update through DSL is not supported on feat branch")
    @pytest.mark.slow
    @pytest.mark.parametrize("Runbook", [DslPausePlayRunbook])
    def test_rb_update(self, Runbook):

        client = get_api_client()
        rb_name = "test_ask_" + str(uuid.uuid4())[-10:]

        rb = upload_runbook(client, rb_name, Runbook)
        rb_state = rb["status"]["state"]
        rb_uuid = rb["metadata"]["uuid"]
        print(">> Runbook state: {}".format(rb_state))
        assert rb_state == "ACTIVE"
        assert rb_name == rb["spec"]["name"]
        assert rb_name == rb["metadata"]["name"]

        # reading the runbook using get call
        print("\n>>Reading Runbook")
        res, err = client.runbook.read(rb_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        else:
            assert res.ok is True
            res = res.json()
            task_list = res["spec"]["resources"]["runbook"]["task_definition_list"]
            assert len(task_list) == 6
            assert rb_name == res["spec"]["name"]
            assert rb_name == res["metadata"]["name"]
            assert rb_name == res["metadata"]["name"]
            print(">> Get call to runbook is successful >>")

        # updating the runbook
        # TODO have to update this with updated runbook
        rb = update_runbook(client, rb_name, DslPausePlayRunbook)
        rb_state = rb["status"]["state"]
        rb_uuid = rb["metadata"]["uuid"]
        print(">> Runbook state: {}".format(rb_state))
        assert rb_state == "ACTIVE"
        assert rb_name == rb["spec"]["name"]
        assert rb_name == rb["metadata"]["name"]

        # reading the runbook using get call
        print("\n>>Reading Runbook")
        res, err = client.runbook.read(rb_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        else:
            assert res.ok is True
            res = res.json()
            task_list = res["spec"]["resources"]["runbook"]["task_definition_list"]
            assert len(task_list) == 5
            assert rb_name == res["spec"]["name"]
            assert rb_name == res["metadata"]["name"]
            assert rb_name == res["metadata"]["name"]
            print(">> Get call to runbook is successful >>")

        # deleting runbook
        print("\n>>Deleting runbook")
        res, err = client.runbook.delete(rb_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        else:
            assert res.ok is True
            res = res.json()
            print("API Response: {}".format(res["description"]))
            print(">> Delete call to runbook is successful >>")
