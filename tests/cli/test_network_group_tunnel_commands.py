import pytest
import json
import uuid
import traceback
import click
from distutils.version import LooseVersion as LV
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.config import get_context
from calm.dsl.builtins import read_local_file
from calm.dsl.store import Version
from calm.dsl.log import get_logging_handle
from calm.dsl.cli.main import get_api_client
from calm.dsl.builtins.models.metadata_payload import reset_metadata_obj

LOG = get_logging_handle(__name__)

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
DSL_NETWORK_GROUP_TUNNEL_PATH = "tests/network_group_tunnel/network_group_tunnel.py"

# calm_version
CALM_VERSION = Version.get_version("Calm")


@pytest.mark.skipif(
    LV(CALM_VERSION) < LV("3.5.0") or not DSL_CONFIG["IS_VPC_ENABLED"],
    reason="Overlay Subnets can be used in Calm v3.5.0+ blueprints or VPC is disabled on the setup",
)
class TestNetworkGroupTunnelCommands:
    def setup_method(self):
        """ "Reset the context changes"""

        # Resetting context
        ContextObj = get_context()
        ContextObj.reset_configuration()

        # Resetting metadata object
        reset_metadata_obj()

    def teardown_method(self):
        """ "Reset the context changes"""

        # Resetting context
        ContextObj = get_context()
        ContextObj.reset_configuration()

        # Resetting metadata object
        reset_metadata_obj()

    def test_network_group_tunnels_list(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get", "network-group-tunnels"])
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
            pytest.fail("Network Group Tunnel Get failed")
        LOG.info("Success")

    def test_network_group_list(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get", "network-groups"])
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
            pytest.fail("Network Group Tunnel Get failed")
        LOG.info("Success")

    def _test_create_network_group_tunnel(self):

        runner = CliRunner()
        LOG.info(
            "Creating NetworkGroup Tunnel file at {}".format(
                DSL_NETWORK_GROUP_TUNNEL_PATH
            )
        )
        self.tunnel_name = "TestCRUDTunnel_{}".format(str(uuid.uuid4())[0:6])
        result = runner.invoke(
            cli,
            [
                "-vv",
                "create",
                "network-group-tunnel",
                "--file={}".format(DSL_NETWORK_GROUP_TUNNEL_PATH),
                "--name={}".format(self.tunnel_name),
            ],
        )

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
            pytest.fail("Project compile command failed")
        LOG.info("Success")

    def _test_network_group_tunnel_describe_out_text(self):
        runner = CliRunner()
        LOG.info("Testing 'calm describe network-group-tunnel --out text' command")
        result = runner.invoke(
            cli, ["describe", "network-group-tunnel", self.tunnel_name]
        )
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
            pytest.fail("Network-Group-Tunnel Describe call failed")

        tunnel_name_str = "Name: {}".format(self.tunnel_name)
        ng_tunnel_name_str = "Name: {}".format(self.tunnel_name + "_ng")
        assert tunnel_name_str in result.output
        assert ng_tunnel_name_str in result.output
        LOG.info("Success")

    def _test_network_group_tunnel_describe_out_json(self):

        runner = CliRunner()
        LOG.info("Testing 'calm describe network-group-tunnel --out json' command")
        result = runner.invoke(
            cli, ["describe", "network-group-tunnel", self.tunnel_name, "--out", "json"]
        )
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
            pytest.fail("Project Get call failed")

        tunnel_name_str = '"name": "{}"'.format(self.tunnel_name)
        ng_tunnel_name_str = '"name": "{}"'.format(self.tunnel_name + "_ng")
        assert tunnel_name_str in result.output
        assert ng_tunnel_name_str in result.output
        LOG.info("Success")

    def _test_network_group_tunnel_delete(self):
        runner = CliRunner()
        LOG.info("Testing 'calm delete network-group-tunnel' command")
        result = runner.invoke(
            cli, ["delete", "network-group-tunnel", self.tunnel_name]
        )
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
            pytest.fail("NetworkGroupTunnel delete call failed")
        LOG.info("Success")

    def test_crud_network_group_tunnel(self):

        # Create operation
        self._test_create_network_group_tunnel()

        click.echo("")
        self._test_network_group_tunnel_describe_out_text()

        click.echo("")
        self._test_network_group_tunnel_describe_out_json()

        click.echo("")
        self._test_network_group_tunnel_delete()
