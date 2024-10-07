import pytest
import uuid
from distutils.version import LooseVersion as LV

from calm.dsl.store import Version
from calm.dsl.cli.main import get_api_client
from calm.dsl.cli.constants import RUNLOG
from tests.api_interface.test_runbooks.test_files.vm_endpoints_warning import (
    VMEndpointWithIncorrectID,
    VMEndpointWithNoIP,
    VMEndpointWithIPOutsideSubnet,
    VMEndpointWithOffState,
)
from utils import upload_runbook, poll_runlog_status

# calm_version
CALM_VERSION = Version.get_version("Calm")


@pytest.mark.skipif(
    LV(CALM_VERSION) < LV("3.2.0"),
    reason="Tests are for env changes introduced in 3.2.0",
)
class TestVMEndpointsFailureScenarios:
    @pytest.mark.runbook
    @pytest.mark.regression
    @pytest.mark.parametrize(
        "Runbook, warning_msg",
        [
            pytest.param(
                VMEndpointWithIncorrectID, "No VM Found with the given instance ID"
            ),
            pytest.param(VMEndpointWithNoIP, "VM doesn't have any IP Address"),
            pytest.param(
                VMEndpointWithIPOutsideSubnet,
                "VM doesn't have any IP address that match the subnet range as defined by the given subnet",
            ),
            pytest.param(VMEndpointWithOffState, "VM is not in powered ON State"),
        ],
    )
    def test_warnings_on_vm_endpoint(self, Runbook, warning_msg):
        """
        Test Warnings scenarios on exec tasks over vm endpoint
        """

        client = get_api_client()
        rb_name = "test_warning_vm_endpoint_" + str(uuid.uuid4())[-10:]

        if Runbook == VMEndpointWithIncorrectID:
            # For VMEndpointWithIncorrectID, since the VM ID is incorrect, the runbook upload should fail as endpoint can't be created
            res_json = upload_runbook(
                client, rb_name, Runbook, return_error_response=True
            )
            if LV(CALM_VERSION) >= LV("4.0.0"):
                assert res_json["code"] == 422
            else:
                assert res_json["code"] == 403
            assert res_json["message_list"][0]["reason"] == "ACCESS_DENIED"
            return
        rb = upload_runbook(client, rb_name, Runbook)
        rb_state = rb["status"]["state"]
        rb_uuid = rb["metadata"]["uuid"]
        print(">> Runbook state: {}".format(rb_state))
        assert rb_state == "ACTIVE"
        assert rb_name == rb["spec"]["name"]
        assert rb_name == rb["metadata"]["name"]

        # endpoints generated by this runbook
        endpoint_list = rb["spec"]["resources"].get("endpoint_definition_list", [])

        # running the runbook
        print("\n>>Running the runbook")

        res, err = client.runbook.run(rb_uuid, {})
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        response = res.json()
        runlog_uuid = response["status"]["runlog_uuid"]

        # polling till runbook run gets to terminal state
        state, reasons = poll_runlog_status(
            client, runlog_uuid, RUNLOG.TERMINAL_STATES, maxWait=360
        )

        print(">> Runbook Run state: {}\n{}".format(state, reasons))
        if LV(CALM_VERSION) >= LV("3.9.0"):
            assert state == RUNLOG.STATUS.FAILURE
        else:
            assert state == RUNLOG.STATUS.ERROR

        # Finding the trl id for the shell and escript task (all runlogs for multiple IPs)
        escript_tasks = []
        res, err = client.runbook.list_runlogs(runlog_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        response = res.json()
        entities = response["entities"]
        for entity in entities:
            if (
                entity["status"]["type"] == "task_runlog"
                and entity["status"]["task_reference"]["name"] == "ShellTask"
                and runlog_uuid in entity["status"].get("machine_name", "")
            ):
                reasons = ""
                for reason in entity["status"]["reason_list"]:
                    reasons += reason
                assert warning_msg in reasons
                if LV(CALM_VERSION) >= LV("3.9.0"):
                    assert entity["status"]["state"] == RUNLOG.STATUS.FAILURE
                else:
                    assert entity["status"]["state"] == RUNLOG.STATUS.ERROR
            elif (
                entity["status"]["type"] == "task_runlog"
                and entity["status"]["task_reference"]["name"] == "EscriptTask"
                and runlog_uuid in entity["status"].get("machine_name", "")
            ):
                assert entity["status"]["state"] == RUNLOG.STATUS.SUCCESS
                escript_tasks.append(entity["metadata"]["uuid"])

        # Now checking the output of exec tasks
        for exec_task in escript_tasks:
            res, err = client.runbook.runlog_output(runlog_uuid, exec_task)
            if err:
                pytest.fail("[{}] - {}".format(err["code"], err["error"]))
            runlog_output = res.json()
            output_list = runlog_output["status"]["output_list"]
            assert "Escript Task is Successful" in output_list[0]["output"]

        # delete the runbook
        _, err = client.runbook.delete(rb_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        else:
            print("runbook {} deleted".format(rb_name))

        # delete endpoints generated by this test
        for endpoint in endpoint_list:
            _, err = client.endpoint.delete(endpoint["uuid"])
            if err:
                pytest.fail("[{}] - {}".format(err["code"], err["error"]))

    @pytest.mark.epsilon
    @pytest.mark.parametrize(
        "Runbook, warning_msg",
        [
            pytest.param(
                VMEndpointWithIncorrectID, "No VM Found with the given instance ID"
            ),
        ],
    )
    def test_failures_on_vm_endpoint(self, Runbook, warning_msg):
        """
        Test Warnings scenarios on exec tasks over vm endpoint
        """

        client = get_api_client()
        rb_name = "test_warning_vm_endpoint_" + str(uuid.uuid4())[-10:]

        if Runbook == VMEndpointWithIncorrectID:
            # For VMEndpointWithIncorrectID, since the VM ID is incorrect, the runbook upload should fail as endpoint can't be created
            res_json = upload_runbook(
                client, rb_name, Runbook, return_error_response=True
            )
            if LV(CALM_VERSION) >= LV("4.0.0"):
                assert res_json["code"] == 422
            else:
                assert res_json["code"] == 403
            assert res_json["message_list"][0]["reason"] == "ACCESS_DENIED"
            return

        # TODO: Cleanup the below code
        # As part of CALM-45554, Endpoint Creation will be blocked if incorrect unauthorized VM ID is provided
        # Because of this Runbook Upload will fail for VMEndpointWithIncorrectID.
        # Since the only param for this test is VMEndpointWithIncorrectID, the below code won't be executed

        rb = upload_runbook(client, rb_name, Runbook)
        rb_state = rb["status"]["state"]
        rb_uuid = rb["metadata"]["uuid"]
        print(">> Runbook state: {}".format(rb_state))
        assert rb_state == "ACTIVE"
        assert rb_name == rb["spec"]["name"]
        assert rb_name == rb["metadata"]["name"]

        # endpoints generated by this runbook
        endpoint_list = rb["spec"]["resources"].get("endpoint_definition_list", [])

        # running the runbook
        print("\n>>Running the runbook")

        res, err = client.runbook.run(rb_uuid, {})
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        response = res.json()
        runlog_uuid = response["status"]["runlog_uuid"]

        # polling till runbook run gets to terminal state
        state, reasons = poll_runlog_status(
            client, runlog_uuid, RUNLOG.TERMINAL_STATES, maxWait=360
        )

        print(">> Runbook Run state: {}\n{}".format(state, reasons))
        if LV(CALM_VERSION) >= LV("3.9.0"):
            assert state == RUNLOG.STATUS.FAILURE
        else:
            assert state == RUNLOG.STATUS.ERROR

        # Finding the trl id for the shell and escript task (all runlogs for multiple IPs)
        escript_tasks = []
        res, err = client.runbook.list_runlogs(runlog_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        response = res.json()
        entities = response["entities"]
        for entity in entities:
            if (
                entity["status"]["type"] == "task_runlog"
                and entity["status"]["task_reference"]["name"] == "ShellTask"
                and runlog_uuid in entity["status"].get("machine_name", "")
            ):
                reasons = ""
                for reason in entity["status"]["reason_list"]:
                    reasons += reason
                assert warning_msg in reasons
                if LV(CALM_VERSION) >= LV("3.9.0"):
                    assert entity["status"]["state"] == RUNLOG.STATUS.FAILURE
                else:
                    assert entity["status"]["state"] == RUNLOG.STATUS.ERROR
            elif (
                entity["status"]["type"] == "task_runlog"
                and entity["status"]["task_reference"]["name"] == "EscriptTask"
                and runlog_uuid in entity["status"].get("machine_name", "")
            ):
                assert entity["status"]["state"] == RUNLOG.STATUS.SUCCESS
                escript_tasks.append(entity["metadata"]["uuid"])

        # Now checking the output of exec tasks
        for exec_task in escript_tasks:
            res, err = client.runbook.runlog_output(runlog_uuid, exec_task)
            if err:
                pytest.fail("[{}] - {}".format(err["code"], err["error"]))
            runlog_output = res.json()
            output_list = runlog_output["status"]["output_list"]
            assert "Escript Task is Successful" in output_list[0]["output"]

        # delete the runbook
        _, err = client.runbook.delete(rb_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        else:
            print("runbook {} deleted".format(rb_name))

        # delete endpoints generated by this test
        for endpoint in endpoint_list:
            _, err = client.endpoint.delete(endpoint["uuid"])
            if err:
                pytest.fail("[{}] - {}".format(err["code"], err["error"]))
