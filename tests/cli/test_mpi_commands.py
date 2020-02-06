import pytest
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.api import get_api_client, get_resource_api
from calm.dsl.cli.mpis import get_app_family_list, get_group_data_value


@pytest.mark.slow
class TestMPICommands:
    def test_mpis_list(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get", "marketplace_apps"])
        assert result.exit_code == 0
        if result.exit_code:
            pytest.fail("MPI list call failed")
        print(result.output)

    def test_mpis_list_with_display_all_flag(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get", "marketplace_apps", "--display_all"])
        assert result.exit_code == 0
        if result.exit_code:
            pytest.fail("MPI list call failed")
        print(result.output)

    def test_mpis_list_with_app_family_filter(self):
        runner = CliRunner()
        app_family_list = get_app_family_list()

        input = ["get", "marketplace_apps", "--app_family", ""]
        for app_family in app_family_list:
            input[3] = app_family
            result = runner.invoke(cli, input)
            assert result.exit_code == 0
            if result.exit_code:
                pytest.fail("MPI list call failed")
            print(result.output)

    def test_mpi_describe_with_default_version(self):

        payload = {
            "grouping_attribute": "app_group_uuid",
            "group_count": 48,
            "group_member_count": 1,
            "group_offset": 0,
            "filter_criteria": "marketplace_item_type_list==APP;(app_state==PUBLISHED)",
            "entity_type": "marketplace_item",
            "group_member_attributes": [{"attribute": "name"}],
        }

        client = get_api_client()
        Obj = get_resource_api("groups", client.connection)

        res, err = Obj.create(payload=payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        group = res["group_results"][0]
        entity_data = group["entity_results"][0]["data"]

        mpi_name = get_group_data_value(entity_data, "name")
        runner = CliRunner()
        result = runner.invoke(cli, ["describe", "marketplace_app", mpi_name])
        assert result.exit_code == 0
        if result.exit_code:
            pytest.fail("MPI list call failed")
        print(result.output)

    def test_mpi_describe_with_user_version(self):
        """To describe mpi with given version(cli input)"""

        payload = {
            "grouping_attribute": "app_group_uuid",
            "group_count": 48,
            "group_member_count": 1,
            "group_offset": 0,
            "filter_criteria": "marketplace_item_type_list==APP;(app_state==PUBLISHED)",
            "entity_type": "marketplace_item",
            "group_member_attributes": [
                {"attribute": "name"},
                {"attribute": "version"},
            ],
        }

        client = get_api_client()
        Obj = get_resource_api("groups", client.connection)

        res, err = Obj.create(payload=payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        group = res["group_results"][0]
        entity_data = group["entity_results"][0]["data"]

        mpi_name = get_group_data_value(entity_data, "name")
        mpi_version = get_group_data_value(entity_data, "version")

        runner = CliRunner()
        result = runner.invoke(
            cli, ["describe", "marketplace_app", mpi_name, "--version", mpi_version]
        )
        assert result.exit_code == 0
        if result.exit_code:
            pytest.fail("MPI list call failed")
        print(result.output)

    def test_mpi_launch(self):
        """
            Steps:
                1. Create a blueprint
                2. Submit for approval
                3. Approve and publish to marketplace
                4. Launch the app from marketoplace
        """
        pass
