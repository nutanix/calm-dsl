import json
import time
import pytest

from click.testing import CliRunner
from calm.dsl.cli import main as cli

from calm.dsl.cli.constants import APPLICATION, ERGON_TASK
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


class Application:
    NON_BUSY_APP_STATES = [
        APPLICATION.STATES.STOPPED,
        APPLICATION.STATES.RUNNING,
        APPLICATION.STATES.ERROR,
    ]

    def _wait_for_non_busy_state(self, name, timeout=300):
        runner = CliRunner()
        result = runner.invoke(cli, ["describe", "app", name, "--out=json"])
        app_data = json.loads(result.output)
        LOG.info("App State: {}".format(app_data["status"]["state"]))
        LOG.debug("App Terminal states: {}".format(self.NON_BUSY_APP_STATES))

        is_terminal = True
        poll_interval = 15
        while app_data["status"]["state"] not in self.NON_BUSY_APP_STATES:
            time.sleep(poll_interval)
            result = runner.invoke(cli, ["describe", "app", name, "--out=json"])
            app_data = json.loads(result.output)
            LOG.info("App State: {}".format(app_data["status"]["state"]))
            if timeout <= 0:
                LOG.error("Failed to reach terminal state in 100 seconds")
                LOG.debug("App: {}".format(app_data))
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
