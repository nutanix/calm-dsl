import json
import time

from click.testing import CliRunner
from calm.dsl.cli import main as cli

from calm.dsl.cli.constants import APPLICATION
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

        return is_terminal
