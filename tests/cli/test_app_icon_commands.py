import pytest
import uuid
import sys
from click.testing import CliRunner

from calm.dsl.log import get_logging_handle
from calm.dsl.cli import main as cli
from calm.dsl.api import get_api_client

DSL_BP_FILEPATH = "tests/existing_vm_example/test_existing_vm_bp.py"
APP_ICON_IMAGE_PATH = "tests/cli/images/test_app_icon.jpg"
LOG = get_logging_handle(__name__)


class TestAppIconCommands:
    def setup_method(self):
        """Method to instantiate to created_bp_list and created_app_list"""

        self.created_bp_list = []
        self.created_marketplace_bp_list = []

    def teardown_method(self):
        """Method to delete creates bps and apps during tests"""

        for bp_name in self.created_bp_list:
            LOG.info("Deleting Blueprint {}".format(bp_name))
            runner = CliRunner()
            result = runner.invoke(cli, ["delete", "bp", bp_name])
            assert result.exit_code == 0

        for bp_name, version in self.created_marketplace_bp_list:
            runner = CliRunner()
            result = runner.invoke(
                cli, ["delete", "marketplace_bp", bp_name, "-v", version]
            )
            assert result.exit_code == 0

        self.created_app_list = []
        self.created_marketplace_bp_list = []

    def _create_bp(self, name=None):

        self.created_dsl_bp_name = name or "Test_Existing_VM_DSL_{}".format(
            str(uuid.uuid4())[-10:]
        )
        LOG.info("Creating Bp {}".format(self.created_dsl_bp_name))

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "create",
                "bp",
                "--file={}".format(DSL_BP_FILEPATH),
                "--name={}".format(self.created_dsl_bp_name),
                "--description='Test DSL Blueprint; to delete'",
            ],
        )

        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("Creation of blueprint failed")

        self.created_bp_list.append(self.created_dsl_bp_name)

    def _publish_bp_to_marketplace_manager_with_icon(self):

        self.marketplace_bp_name = "Test_Marketplace_Bp_{}".format(
            str(uuid.uuid4())[-10:]
        )
        self.mpi_version = "1.0.0"

        LOG.info("Publishing bp to marketplace")
        command = [
            "publish",
            "bp",
            self.created_dsl_bp_name,
            "--version={}".format(self.mpi_version),
            "--name={}".format(self.marketplace_bp_name),
            "--icon_name={}".format(self.icon_name),
        ]
        runner = CliRunner()
        result = runner.invoke(cli, command)

        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("Publishing of blueprint as new marketplace item failed")

        self.created_marketplace_bp_list.append(
            (self.marketplace_bp_name, self.mpi_version)
        )

    def test_create_command(self):
        """Test for create app_icon command"""

        runner = CliRunner()
        LOG.info("Running 'calm create app_icon' command")

        self.icon_name = "test_icon{}".format(str(uuid.uuid4())[:10])
        command = [
            "create",
            "app_icon",
            "-f",
            APP_ICON_IMAGE_PATH,
            "-n",
            self.icon_name,
        ]
        result = runner.invoke(cli, command)

        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("Creation of app icon failed")

        LOG.info("App icon created successfully")

        self._test_negative_is_marketplace_icon()
        self._create_bp()
        self._publish_bp_to_marketplace_manager_with_icon()

        self._test_is_marketplace_icon()
        self._test_delete_app_icon()

    def _test_negative_is_marketplace_icon(self):
        """Check app_icon not used for any marketplace icon"""

        client = get_api_client()
        app_icon_name_uuid_map = client.app_icon.get_name_uuid_map()
        self.app_icon_uuid = app_icon_name_uuid_map.get(self.icon_name)

        res, err = client.app_icon.is_marketplace_icon(self.app_icon_uuid)
        if err:
            LOG.error("[{}] - {}".format(err["code"], err["error"]))
            sys.exit(-1)

        res = res.json()
        assert not res[
            "is_marketplaceicon"
        ], "App Icon is not supposed to be marketplace icon"

    def _test_is_marketplace_icon(self):
        """Check app_icon is used for marketplace icon"""

        client = get_api_client()
        res, err = client.app_icon.is_marketplace_icon(self.app_icon_uuid)
        if err:
            LOG.error("[{}] - {}".format(err["code"], err["error"]))
            sys.exit(-1)

        res = res.json()
        assert res["is_marketplaceicon"], "App Icon is supposed to be marketplace icon"

    def _test_delete_app_icon(self):
        """Test for deleting app icon"""

        runner = CliRunner()
        LOG.info("Deleting app icon {}".format(self.icon_name))

        command = ["delete", "app_icon", self.icon_name]
        result = runner.invoke(cli, command)

        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("Deletion of app icon failed")

        LOG.info("App Icon {} deleted successfully")

    def test_get_app_icons(self):
        """Test for listing app icons"""

        runner = CliRunner()
        LOG.info("Testing 'calm get app_icons' command")
        result = runner.invoke(cli, ["get", "app_icons"])
        assert result.exit_code == 0
        if result.exit_code:
            pytest.fail("App icons get call failed")
        LOG.info("Success")

        LOG.info("Testing --marketplace_use flag")
        result = runner.invoke(cli, ["get", "app_icons", "--marketplace_use"])
        assert result.exit_code == 0
        if result.exit_code:
            pytest.fail("App icons get call failed")
        LOG.info("Success")

        LOG.info("Testing limit and offset filter")
        runner = CliRunner()
        result = runner.invoke(cli, ["get", "app_icons"])
        assert result.exit_code == 0
        if result.exit_code:
            pytest.fail("App icons get call failed")
        LOG.info("Success")
