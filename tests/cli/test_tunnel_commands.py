import pytest
import json
import uuid
import traceback
from distutils.version import LooseVersion as LV
from calm.dsl.api.util import is_policy_check_required
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.config import get_context
from calm.dsl.builtins import read_local_file
from calm.dsl.store import Version
from calm.dsl.log import get_logging_handle
from calm.dsl.builtins.models.helper.common import get_policy_status

LOG = get_logging_handle(__name__)
DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))

CALM_VERSION = Version.get_version("Calm")


# if ncm is enabled on smsp (opt-in), then no need to check policy status and run these tests
# if ncm sits in PC (opt-out), then skip tests if policy is disabled.
@pytest.mark.skipif(
    (is_policy_check_required() and not get_policy_status())
    or LV(CALM_VERSION) < LV("4.3.0"),
    reason="Policy is not enabled or Calm version is < 4.3.0, so skipping the test",
)
class TestTunnelCommands:
    def _create_tunnel(self, runner, name):
        result = runner.invoke(
            cli,
            [
                "create",
                "tunnel",
                "--name",
                name,
                "--description",
                "Temp tunnel description",
            ],
        )
        if result.exit_code:
            raise Exception("Setup: Failed to create tunnel")

    def _cleanup_tunnel(self, runner, name):
        result = runner.invoke(cli, ["delete", "tunnels", name])
        if result.exit_code:
            LOG.warning("Cleanup: Failed to delete tunnel '{}'".format(name))

    def test_create_tunnel(self):
        self.tunnel_name = "TestTunnel_{}".format(str(uuid.uuid4())[:8])
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "create",
                "tunnel",
                "--name",
                self.tunnel_name,
                "--description",
                "Test tunnel description",
            ],
        )
        if result.exit_code:
            LOG.debug(
                json.dumps(
                    {"Output": result.output, "Exception": str(result.exception)},
                    indent=4,
                    separators=(",", ": "),
                )
            )
            LOG.debug(
                "Traceback: \n{}".format(
                    "".join(traceback.format_tb(result.exc_info[2]))
                )
            )
            pytest.fail("Tunnel create command failed")
        LOG.info("Tunnel created successfully")
        self._cleanup_tunnel(runner, self.tunnel_name)

    def test_update_tunnel(self):
        runner = CliRunner()
        self.tunnel_name = "TestTunnel_{}".format(str(uuid.uuid4())[:8])
        new_name = self.tunnel_name + "_updated"
        self._create_tunnel(runner, self.tunnel_name)
        result = runner.invoke(
            cli, ["update", "tunnel", self.tunnel_name, "--new-name", new_name]
        )
        if result.exit_code:
            LOG.debug(
                json.dumps(
                    {"Output": result.output, "Exception": str(result.exception)},
                    indent=4,
                    separators=(",", ": "),
                )
            )
            LOG.debug(
                "Traceback: \n{}".format(
                    "".join(traceback.format_tb(result.exc_info[2]))
                )
            )
            pytest.fail("Tunnel update failed")
        LOG.info("Tunnel updated successfully")
        self._cleanup_tunnel(runner, new_name)

    def test_describe_tunnel_text(self):
        runner = CliRunner()
        self.tunnel_name = "TestTunnel_{}".format(str(uuid.uuid4())[:8])
        self._create_tunnel(runner, self.tunnel_name)
        result = runner.invoke(cli, ["describe", "tunnel", self.tunnel_name])
        if result.exit_code:
            LOG.debug(
                json.dumps(
                    {"Output": result.output, "Exception": str(result.exception)},
                    indent=4,
                    separators=(",", ": "),
                )
            )
            LOG.debug(
                "Traceback: \n{}".format(
                    "".join(traceback.format_tb(result.exc_info[2]))
                )
            )
            pytest.fail("Tunnel describe failed")
        assert f"Name: {self.tunnel_name}" in result.output
        LOG.info("Tunnel described in text format successfully")
        self._cleanup_tunnel(runner, self.tunnel_name)

    def test_describe_tunnel_json(self):
        runner = CliRunner()
        self.tunnel_name = "TestTunnel_{}".format(str(uuid.uuid4())[:8])
        self._create_tunnel(runner, self.tunnel_name)
        result = runner.invoke(
            cli, ["describe", "tunnel", self.tunnel_name, "--out", "json"]
        )
        if result.exit_code:
            LOG.debug(
                json.dumps(
                    {"Output": result.output, "Exception": str(result.exception)},
                    indent=4,
                    separators=(",", ": "),
                )
            )
            LOG.debug(
                "Traceback: \n{}".format(
                    "".join(traceback.format_tb(result.exc_info[2]))
                )
            )
            pytest.fail("Tunnel describe (JSON) failed")

        assert f'"name": "{self.tunnel_name}"' in result.output
        LOG.info("Tunnel described in JSON format successfully")

        self._cleanup_tunnel(runner, self.tunnel_name)

    def test_delete_tunnel(self):
        runner = CliRunner()
        self.tunnel_name = "TestTunnel_{}".format(str(uuid.uuid4())[:8])
        self._create_tunnel(runner, self.tunnel_name)
        result = runner.invoke(cli, ["delete", "tunnels", self.tunnel_name])
        if result.exit_code:
            LOG.debug(
                json.dumps(
                    {"Output": result.output, "Exception": str(result.exception)},
                    indent=4,
                    separators=(",", ": "),
                )
            )
            LOG.debug(
                "Traceback: \n{}".format(
                    "".join(traceback.format_tb(result.exc_info[2]))
                )
            )
            pytest.fail("Tunnel delete failed")
        LOG.info("Tunnel deleted successfully")

    def test_get_tunnels(self):
        runner = CliRunner()

        result = runner.invoke(cli, ["get", "tunnels", "--limit", "5"])
        if result.exit_code:
            LOG.debug(
                json.dumps(
                    {"Output": result.output, "Exception": str(result.exception)},
                    indent=4,
                    separators=(",", ": "),
                )
            )
            LOG.debug(
                "Traceback: \n{}".format(
                    "".join(traceback.format_tb(result.exc_info[2]))
                )
            )
            pytest.fail("Tunnel list fetch failed")
        LOG.info("Tunnel list fetched successfully")
