import pytest
import uuid
import json

from calm.dsl.cli.main import get_api_client
from calm.dsl.cli.constants import RUNLOG
from tests.api_interface.test_runbooks.test_files.http_task import (
    get_http_task_runbook,
    HTTPTaskWithValidations,
    HTTPTaskWithoutAuth,
    HTTPTaskWithIncorrectCode,
    HTTPTaskWithFailureState,
    HTTPTaskWithUnsupportedURL,
    HTTPTaskWithUnsupportedPayload,
    HTTPTaskWithTLSVerify,
    HTTPTaskWithIncorrectAuth,
    HTTPHeadersWithMacro,
    HTTPRelativeURLWithMacro,
    HTTPEndpointWithMultipleURLs,
)
from utils import upload_runbook, poll_runlog_status

from distutils.version import LooseVersion as LV
from calm.dsl.store import Version
from calm.dsl.builtins.models.utils import read_local_file

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
CALM_VERSION = Version.get_version("Calm")


class TestHTTPTasks:
    @pytest.mark.runbook
    @pytest.mark.regression
    @pytest.mark.parametrize(
        "endpoint_file",
        [
            "http_endpoint_payload.json",
            pytest.param(
                "http_tunnel_endpoint.json",
                marks=pytest.mark.skipif(
                    LV(CALM_VERSION) < LV("3.5.0")
                    or not DSL_CONFIG.get("IS_VPC_ENABLED", False),
                    reason="VPC Tunnels can be used in Calm v3.5.0+ or VPC is disabled on the setup",
                ),
            ),
        ],
    )
    def test_http_task(self, endpoint_file):
        """test_http_task, test_http_task_outputin_set_variable,
        test_relative_url_http, test_http_task_without_tls_verify"""

        client = get_api_client()
        rb_name = "test_httptask_" + str(uuid.uuid4())[-10:]

        HTTPTask = get_http_task_runbook(endpoint_file, config_file=DSL_CONFIG)
        rb = upload_runbook(client, rb_name, HTTPTask)
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
                and entity["status"]["task_reference"]["name"] == "ExecTask"
            ):
                exec_task = entity["metadata"]["uuid"]

        # Now checking the output of exec task
        res, err = client.runbook.runlog_output(runlog_uuid, exec_task)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        runlog_output = res.json()
        output_list = runlog_output["status"]["output_list"]
        assert output_list[0]["output"] == "HTTP\n"

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

    @pytest.mark.runbook
    @pytest.mark.regression
    def test_http_validations(self):
        """test_response_field_blank_http, test_http_without_any_target,
        test_http_task_with_json_content_type"""

        client = get_api_client()
        rb_name = "test_httptask_" + str(uuid.uuid4())[-10:]

        rb = upload_runbook(client, rb_name, HTTPTaskWithValidations)
        rb_state = rb["status"]["state"]
        rb_uuid = rb["metadata"]["uuid"]
        print(">> Runbook state: {}".format(rb_state))
        assert rb_state == "DRAFT"
        assert rb_name == rb["spec"]["name"]
        assert rb_name == rb["metadata"]["name"]

        # checking validation errors
        task_list = rb["status"]["resources"]["runbook"]["task_definition_list"]
        for task in task_list:
            if task["type"] == "HTTP":
                validation_errors = ""
                for message in task["message_list"]:
                    validation_errors += message["message"]
                assert (
                    "No default endpoint or endpoint at task level or inherited endpoint"
                    in validation_errors
                )
                assert (
                    "Atleast one of expected response status and response code are required."
                    in validation_errors
                )

        # delete the runbook
        _, err = client.runbook.delete(rb_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        else:
            print("runbook {} deleted".format(rb_name))

    @pytest.mark.runbook
    @pytest.mark.regression
    def test_http_without_auth(self):
        """test_http_get_task_no_auth, test_http_default_target,
        test_http_task_with_html_content_type"""

        client = get_api_client()
        rb_name = "test_httptask_" + str(uuid.uuid4())[-10:]

        rb = upload_runbook(client, rb_name, HTTPTaskWithoutAuth)
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
        state, reasons = poll_runlog_status(client, runlog_uuid, RUNLOG.TERMINAL_STATES)

        print(">> Runbook Run state: {}\n{}".format(state, reasons))
        assert state == RUNLOG.STATUS.SUCCESS

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

    @pytest.mark.runbook
    @pytest.mark.regression
    def test_http_incorrect_response_code(self):
        """test_expected_response_check_with_different_val_than_expected_val_http"""

        client = get_api_client()
        rb_name = "test_httptask_" + str(uuid.uuid4())[-10:]

        rb = upload_runbook(client, rb_name, HTTPTaskWithIncorrectCode)
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
        state, reasons = poll_runlog_status(client, runlog_uuid, RUNLOG.TERMINAL_STATES)

        print(">> Runbook Run state: {}\n{}".format(state, reasons))
        assert state == RUNLOG.STATUS.SUCCESS

        # Finding the task_uuid for the http task
        res, err = client.runbook.list_runlogs(runlog_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        response = res.json()
        entities = response["entities"]
        for entity in entities:
            if (
                entity["status"]["type"] == "task_runlog"
                and entity["status"]["task_reference"]["name"] == "HTTPTask"
                and runlog_uuid in entity["status"].get("machine_name", "")
            ):
                http_task = entity["metadata"]["uuid"]

        # Now checking the output of exec task
        res, err = client.runbook.runlog_output(runlog_uuid, http_task)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        runlog_output = res.json()
        output_list = runlog_output["status"]["output_list"]
        assert "Defaulting to HTTP return status" in output_list[0]["output"]

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

    @pytest.mark.runbook
    @pytest.mark.regression
    @pytest.mark.parametrize(
        "Helper",
        [
            (
                HTTPTaskWithFailureState,
                "Status code 200 matched with expected response. Result: FAILURE\nFAILED!",
            ),
            (HTTPTaskWithUnsupportedPayload, "'payload' was unexpected"),
            pytest.param(
                (
                    HTTPTaskWithUnsupportedURL,
                    "The requested URL was not found on the server.",
                ),
            ),
            (HTTPTaskWithTLSVerify, "Error :Certificate has expired"),
            (HTTPTaskWithIncorrectAuth, "AUTHENTICATION_REQUIRED"),
        ],
    )
    def test_http_failure_scenarios(self, Helper):
        """test_http_task_failure_status_code_check,
        test_unsupported_payload_json,
        test_unsupprted_url_http,
        test_http_task_with_tls_verify,
        test_http_task_with_incorrect_auth
        """
        Runbook = Helper[0]
        TaskOutput = Helper[1]

        client = get_api_client()
        rb_name = "test_httptask_" + str(uuid.uuid4())[-10:]

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
        state, reasons = poll_runlog_status(client, runlog_uuid, RUNLOG.TERMINAL_STATES)

        print(">> Runbook Run state: {}\n{}".format(state, reasons))
        assert state in RUNLOG.FAILURE_STATES

        # Finding the task_uuid for the http task
        res, err = client.runbook.list_runlogs(runlog_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        response = res.json()
        entities = response["entities"]
        for entity in entities:
            if (
                entity["status"]["type"] == "task_runlog"
                and entity["status"]["task_reference"]["name"] == "HTTPTask"
            ):
                http_task = entity["metadata"]["uuid"]

        # Now checking the output of exec task
        res, err = client.runbook.runlog_output(runlog_uuid, http_task)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        runlog_output = res.json()
        output_list = runlog_output["status"]["output_list"]
        assert TaskOutput in output_list[0]["output"]

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

    @pytest.mark.regression
    @pytest.mark.runbook
    @pytest.mark.parametrize(
        "Runbook",
        [HTTPHeadersWithMacro, HTTPRelativeURLWithMacro, HTTPEndpointWithMultipleURLs],
    )
    def test_macros_in_http_header(self, Runbook):
        """test_macros_in_http_header, test_variable_in_relative_url"""

        client = get_api_client()
        rb_name = "test_httptask_" + str(uuid.uuid4())[-10:]

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
        state, reasons = poll_runlog_status(client, runlog_uuid, RUNLOG.TERMINAL_STATES)

        print(">> Runbook Run state: {}\n{}".format(state, reasons))
        assert state == RUNLOG.STATUS.SUCCESS

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
