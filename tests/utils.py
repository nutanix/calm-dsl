import json
from logging import exception
import time
import traceback
import pytest

from click.testing import CliRunner
from calm.dsl.cli import main as cli

from calm.dsl.cli.constants import APPLICATION, ERGON_TASK, RUNLOG
from calm.dsl.log import get_logging_handle
from calm.dsl.api import get_client_handle_obj
from calm.dsl.api.connection import REQUEST
from calm.dsl.cli.main import get_api_client


VPC_TUNNEL_NAME = "vpc_name_1"
LOG = get_logging_handle(__name__)


class Application:
    NON_BUSY_APP_STATES = [
        APPLICATION.STATES.STOPPED,
        APPLICATION.STATES.RUNNING,
        APPLICATION.STATES.ERROR,
    ]

    def _wait_for_non_busy_state(self, name, timeout=300):
        return self._wait_for_states(name, self.NON_BUSY_APP_STATES, timeout)

    def _wait_for_states(self, name, states, timeout=100):
        LOG.info("Waiting for states: {}".format(states))
        runner = CliRunner()
        result = runner.invoke(cli, ["describe", "app", name, "--out=json"])
        if result.exit_code:
            cli_res_dict = {"Output": result.output, "Exception": str(result.exception)}
            LOG.debug(
                "Cli Response: {}".format(
                    json.dumps(cli_res_dict, indent=4, separators=(",", ": "))
                )
            )
            LOG.debug(
                "Traceback: \n{}".format(
                    "".join(traceback.format_tb(result.exc_info[2]))
                )
            )
        app_data = json.loads(result.output)
        LOG.info("App State: {}".format(app_data["status"]["state"]))
        LOG.debug("App Terminal states: {}".format(states))

        is_terminal = True
        poll_interval = 15

        state = app_data["status"]["state"]
        while state not in states:
            time.sleep(poll_interval)
            result = runner.invoke(cli, ["describe", "app", name, "--out=json"])
            app_data = json.loads(result.output)
            state = app_data["status"]["state"]
            LOG.debug("App State: {}".format(state))
            if timeout <= 0:
                LOG.error("Timed out before reaching desired state")
                is_terminal = False
                break
            timeout -= poll_interval
        LOG.debug("App data: {}".format(app_data))

        return is_terminal

    def get_substrates_platform_data(
        self, name, substrate_name=None, with_metadata=False
    ):
        """
        This routine returns platform data of a vm
        """
        runner = CliRunner()
        result = runner.invoke(cli, ["-vvvvv", "describe", "app", name, "--out=json"])
        app_data = {}
        try:
            app_data = json.loads(result.output)
        except Exception as exp:
            LOG.error("App data: {}".format(result.output))

        platform_data_str = ""
        for substrate in app_data["status"]["resources"]["deployment_list"]:

            if not substrate_name:
                platform_data_str = substrate["substrate_configuration"][
                    "element_list"
                ][0]["platform_data"]

            elif substrate["substrate_configuration"]["name"] == substrate_name:
                platform_data_str = substrate["substrate_configuration"][
                    "element_list"
                ][0]["platform_data"]

            if platform_data_str:
                platform_data_dict = json.loads(platform_data_str)
                if with_metadata:
                    return platform_data_dict
                return platform_data_dict["status"]

        return None

    def execute_actions(self, actions, app):
        "This routine execute actions"
        client = get_api_client()
        app_uuid = app["metadata"]["uuid"]
        app_spec = app["spec"]
        LOG.info(
            "Action Run Stage: Performing actions on application {}".format(app_uuid)
        )
        for action_name in actions:
            calm_action_name = "action_" + action_name.lower()
            LOG.info(
                "Action Run Stage. Running action {} on application {}".format(
                    action_name, app_uuid
                )
            )
            action = next(
                action
                for action in app_spec["resources"]["action_list"]
                if action["name"] == calm_action_name or action["name"] == action_name
            )
            if not action:
                pytest.fail(
                    "Action Run Stage: No action found matching name {}".format(
                        action_name
                    )
                )

            action_id = action["uuid"]

            app.pop("status", None)
            app["spec"] = {
                "args": [],
                "target_kind": "Application",
                "target_uuid": app_uuid,
            }
            res, err = client.application.run_action(app_uuid, action_id, app)
            if err:
                pytest.fail(
                    "Action Run Stage: running action failed [{}] - {}".format(
                        err["code"], err["error"]
                    )
                )

            response = res.json()
            runlog_uuid = response["status"]["runlog_uuid"]
            LOG.info(f"Runlog uuid of custom action triggered {runlog_uuid}")

            url = client.application.ITEM.format(app_uuid) + "/app_runlogs/list"
            payload = {"filter": "root_reference=={}".format(runlog_uuid)}

            maxWait = 5 * 60
            count = 0
            poll_interval = 10
            while count < maxWait:
                # call status api
                res, err = client.application.poll_action_run(url, payload)
                if err:
                    raise Exception("[{}] - {}".format(err["code"], err["error"]))
                response = res.json()
                entities = response["entities"]
                wait_over = False
                if len(entities):
                    sorted_entities = sorted(
                        entities, key=lambda x: int(x["metadata"]["creation_time"])
                    )
                    for runlog in sorted_entities:
                        state = runlog["status"]["state"]
                        if state in RUNLOG.FAILURE_STATES:
                            pytest.fail(
                                "Action Run Stage: action {} failed".format(action_name)
                            )
                            break
                        elif state not in RUNLOG.TERMINAL_STATES:
                            LOG.info(
                                "Action Run Stage: Action {} is in process".format(
                                    action_name
                                )
                            )
                            break
                        else:
                            wait_over = True

                if wait_over:
                    LOG.info(
                        "Action Run Stage: Action {} completed".format(action_name)
                    )
                    break

                count += poll_interval
                time.sleep(poll_interval)

            if count >= maxWait:
                pytest.fail(
                    "Action Run Stage: action {} is not completed in 5 minutes".format(
                        action_name
                    )
                )


class Task:
    def poll_task_to_state(
        self,
        client,
        task_uuid,
        expected_state=ERGON_TASK.STATUS.SUCCEEDED,
        duration=900,
    ):
        """routine will poll for task to come in specific state"""

        def get_task(client, task_uuid):
            res, err = client.nutanix_task.read(task_uuid)
            if err:
                LOG.error(err)
                pytest.fail(res)
            return res.json()

        task_payload = get_task(client, task_uuid)
        poll_interval = 15
        while task_payload["status"] not in ERGON_TASK.TERMINAL_STATES:
            time.sleep(poll_interval)
            if duration <= 0:
                break

            task_payload = get_task(client, task_uuid)
            duration -= poll_interval

        if task_payload["status"] != expected_state:
            LOG.debug(task_payload)
            pytest.fail("Task went to {} state".format(task_payload["status"]))

        return task_payload


class ReportPortal(object):
    def __init__(self, token):

        self.headers = {"Authorization": str(token)}
        self.host = "rp.calm.nutanix.com/api/v1/calm"
        self.client = get_client_handle_obj(
            host=self.host, port=None, scheme=REQUEST.SCHEME.HTTP
        )
        self.client.connection.session.headers = self.headers

    def get_launch_id(self, run_name, run_number):
        """
        This routine gets the launch id for the given runname and number
        Args:
            run_name(str): Report portal run name
            run_number(int): Report portal run number
        Returns:
            (str) launch id
        """
        endpoint = "launch?page.size=50&page=1"
        response, _ = self.client.connection._call(method="get", endpoint=endpoint)
        response = response.json()

        total_pages = int(response["page"]["totalPages"]) + 1

        for page in range(1, total_pages):
            endpoint = "launch?page.size=50&page.page={}&page.sort=start_time,number%2CDESC".format(
                page
            )
            launches, _ = self.client.connection._call(method="get", endpoint=endpoint)
            launches = json.loads(launches.content)

            for launch in launches["content"]:
                if launch["name"] == run_name and launch["number"] == run_number:
                    LOG.info(
                        "Launch id of run name: {}, number: {} is {}".format(
                            run_name, run_number, launch["id"]
                        )
                    )
                    return launch["id"]

        LOG.warning(
            "Launch id of run name: {}, number: {} is not found".format(
                run_name, run_number
            )
        )

    def get_tests(self, launch_id, query_parm, only_test_names=True):
        """
        This routine gets the tests for the given launch id and query_param
        Args:
            launch_id(str): Launch id
            query_parm(str): query_parm supported by report portal
            only_test_names(bool): Return only test name
        Returns:
            (list) list of test names
        """
        endpoint = "item?page.size=50&filter.eq.launch={}".format(launch_id)
        query_parm = endpoint + query_parm if query_parm else endpoint

        response, _ = self.client.connection._call(method="get", endpoint=endpoint)
        response = json.loads(response.content)

        total_pages = int(response["page"]["totalPages"]) + 1
        all_tests = list()
        for page in range(1, total_pages):
            endpoint = "item?page.page={}&page.size=50&filter.eq.launch={}&filter.in.issue$issue_type=TI001".format(
                page, launch_id
            )
            tests, _ = self.client.connection._call(method="get", endpoint=endpoint)
            tests = json.loads(tests.content)
            all_tests.extend(tests["content"])

        if not only_test_names:
            return all_tests
        all_test_name_list = list()
        for test in all_tests:
            test_full_name_split = test["name"].split("::")
            test_name = test_full_name_split[len(test_full_name_split) - 1]
            all_test_name_list.append(test_name)
        return all_test_name_list


def get_vpc_project(config):
    project_name = "default"
    vpc_enabled = config.get("IS_VPC_ENABLED", False)
    if not vpc_enabled:
        return {"name": project_name, "uuid": ""}

    return {
        "name": config.get("VPC_PROJECTS", {})
        .get("PROJECT1", {})
        .get("NAME", project_name),
        "uuid": config.get("VPC_PROJECTS", {}).get("PROJECT1", {}).get("UUID", ""),
    }


def get_vpc_tunnel_using_account(config):
    vpc = ""  # set default, if found set that value
    accounts = config.get("ACCOUNTS", {}).get("NUTANIX_PC", [])
    for acc in accounts:
        if acc.get("NAME") == "NTNX_LOCAL_AZ":
            for subnet in acc.get("OVERLAY_SUBNETS", []):
                if subnet.get("VPC", "") == VPC_TUNNEL_NAME:
                    vpc = VPC_TUNNEL_NAME
                    break

    vpc_tunnel = config.get("VPC_TUNNELS", {}).get("NTNX_LOCAL_AZ", {}).get(vpc, {})
    return {"name": vpc_tunnel.get("name", ""), "uuid": vpc_tunnel.get("uuid", "")}


def get_approval_project(config):
    policy_enabled = config.get("IS_POLICY_ENABLED", False)
    if not policy_enabled:
        raise exception("No Approval Policy Project Found")
    project_name = config.get("POLICY_PROJECTS", {}).get("PROJECT1", {}).get("NAME", "")
    return project_name


def poll_runlog_status(
    client, runlog_uuid, expected_states, poll_interval=10, maxWait=300
):
    """
    This routine polls for 5mins till the runlog gets into the expected state
    Args:
        client (obj): client object
        runlog_uuid (str): runlog id
        expected_states (list): list of expected states
    Returns:
        (str, list): returns final state of the runlog and reasons list
    """
    count = 0
    while count < maxWait:
        res, err = client.runbook.poll_action_run(runlog_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        response = res.json()
        LOG.debug(response)
        state = response["status"]["state"]
        reasons = response["status"]["reason_list"]
        if state in expected_states:
            break
        count += poll_interval
        time.sleep(poll_interval)

    return state, reasons or []


def poll_runlog_status_policy(
    client, expected_states, url, payload, poll_interval=10, maxWait=300
):
    """
    This routine polls policy for 5mins till the runlog gets into the expected state
    Args:
        client (obj): client object
        expected_states (list): list of expected states
        url (str): url to poll
        payload (dict): payload used for polling
    Returns:
        (str, list): returns final state of the runlog and reasons list
    """
    count = 0
    while count < maxWait:
        res, err = client.application.poll_action_run(url, payload)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        response = res.json()
        entity = response.get("entities")
        LOG.info(json.dumps(response))
        if entity:
            state = entity[0]["status"]["state"]
            reasons = entity[0]["status"]["reason_list"]
            if state in expected_states:
                break
        count += poll_interval
        time.sleep(poll_interval)

    return state, reasons or []


def get_escript_language_from_version(script_version="static"):
    """Gets escript language for dsl based on escript_version
    Args:
        script_version(str): Escript version/type: static or static_Py3
    Returns:
        script_language(str): Escript DSL specific language:
            python2- '', '.py2';
            python3- '.py3';
    """
    if script_version == "static_py3":
        script_language = ".py3"
    else:
        script_language = ""  # we can use .py2 as well for static versions
    return script_language
