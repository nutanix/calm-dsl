import pytest

import json
import traceback
from click.testing import CliRunner
import uuid

from calm.dsl.cli import main as cli
from calm.dsl.log import get_logging_handle
from calm.dsl.config import get_context
from calm.dsl.api import get_api_client
from calm.dsl.builtins.models.metadata_payload import reset_metadata_obj
from calm.dsl.cli.accounts import create_account_from_dsl


LOG = get_logging_handle(__name__)


AHV_ACCOUNT_JSON_FILEPATH = "tests/example_accounts/json_payload/test_ahv_account.json"
AWS_ACCOUNT_JSON_FILEPATH = "tests/example_accounts/json_payload/test_aws_account.json"
AWS_C2S_ACCOUNT_JSON_FILEPATH = (
    "tests/example_accounts/json_payload/test_aws_c2s_account.json"
)
AZURE_ACCOUNT_JSON_FILEPATH = (
    "tests/example_accounts/json_payload/test_azure_account.json"
)
GCP_ACCOUNT_JSON_FILEPATH = "tests/example_accounts/json_payload/test_gcp_account.json"
K8S_VANILLA_ACCOUNT_JSON_BASIC_AUTH_FILEPATH = (
    "tests/example_accounts/json_payload/test_k8s_vanilla_account_basic_auth.json"
)
K8S_VANILLA_ACCOUNT_JSON_CA_CERTIFICATE_AUTH_FILEPATH = "tests/example_accounts/json_payload/test_k8s_vanilla_account_ca_certificate_auth.json"
K8S_VANILLA_ACCOUNT_JSON_CLIENT_CERTIFICATE_AUTH_FILEPATH = "tests/example_accounts/json_payload/test_k8s_vanilla_account_client_certificate_auth.json"
K8S_VANILLA_ACCOUNT_JSON_SERVICE_ACCOUNT_AUTH_FILEPATH = "tests/example_accounts/json_payload/test_k8s_vanilla_account_service_account_auth.json"
VMWARE_ACCOUNT_JSON_FILEPATH = (
    "tests/example_accounts/json_payload/test_vmware_account.json"
)
NDB_ACCOUNT_JSON_FILEPATH = "tests/example_accounts/json_payload/test_ndb_account.json"
CREDENTIAL_PROVIDER_ACCOUNT_JSON_FILEPATH = (
    "tests/example_accounts/json_payload/test_credential_provider_account.json"
)


DSL_AHV_ACCOUNT_FILEPATH = "tests/example_accounts/test_ahv_account.py"
DSL_AWS_ACCOUNT_FILEPATH = "tests/example_accounts/test_aws_account.py"
DSL_AWS_C2S_ACCOUNT_FILEPATH = "tests/example_accounts/test_aws_c2s_account.py"
DSL_AZURE_ACCOUNT_FILEPATH = "tests/example_accounts/test_azure_account.py"
DSL_GCP_ACCOUNT_FILEPATH = "tests/example_accounts/test_gcp_account.py"
DSL_K8S_KARBON_ACCOUNT_FILEPATH = "tests/example_accounts/test_k8s_karbon_account.py"
DSL_K8S_VANILLA_ACCOUNT_BASIC_AUTH_FILEPATH = (
    "tests/example_accounts/test_k8s_vanilla_account_basic_auth.py"
)
DSL_K8S_VANILLA_ACCOUNT_CA_CERTIFICATE_AUTH_FILEPATH = (
    "tests/example_accounts/test_k8s_vanilla_account_ca_certificate_auth.py"
)
DSL_K8S_VANILLA_ACCOUNT_CLIENT_CERTIFICATE_AUTH_FILEPATH = (
    "tests/example_accounts/test_k8s_vanilla_account_client_certificate_auth.py"
)
DSL_K8S_VANILLA_ACCOUNT_SERVICE_ACCOUNT_AUTH_FILEPATH = (
    "tests/example_accounts/test_k8s_vanilla_account_service_account_auth.py"
)
DSL_VMWARE_ACCOUNT_FILEPATH = "tests/example_accounts/test_vmware_account.py"
DSL_NDB_ACCOUNT_FILEPATH = "tests/example_accounts/ndb_account.py"
DSL_CREDENTIAL_PROVIDER_ACCOUNT_FILEPATH = (
    "tests/example_accounts/test_credential_provider_account.py"
)

DSL_AHV_UPDATE_ACCOUNT_FILEPATH = (
    "tests/example_accounts/updated_accounts/test_update_ahv_account.py"
)
DSL_AWS_UPDATE_ACCOUNT_FILEPATH = (
    "tests/example_accounts/updated_accounts/test_update_aws_account.py"
)
DSL_AWS_C2S_UPDATE_ACCOUNT_FILEPATH = (
    "tests/example_accounts/updated_accounts/test_update_aws_c2s_account.py"
)
DSL_AZURE_UPDATE_ACCOUNT_FILEPATH = (
    "tests/example_accounts/updated_accounts/test_update_azure_account.py"
)
DSL_GCP_UPDATE_ACCOUNT_FILEPATH = (
    "tests/example_accounts/updated_accounts/test_update_gcp_account.py"
)
DSL_K8S_VANILLA_UPDATE_ACCOUNT_BASIC_AUTH_FILEPATH = "tests/example_accounts/updated_accounts/test_update_k8s_vanilla_account_basic_auth.py"
DSL_K8S_VANILLA_UPDATE_ACCOUNT_CA_CERTIFICATE_AUTH_FILEPATH = "tests/example_accounts/updated_accounts/test_update_k8s_vanilla_account_ca_certificate_auth.py"
DSL_K8S_VANILLA_UPDATE_ACCOUNT_CLIENT_CERTIFICATE_AUTH_FILEPATH = "tests/example_accounts/updated_accounts/test_update_k8s_vanilla_account_client_certificate_auth.py"
DSL_K8S_VANILLA_UPDATE_ACCOUNT_SERVICE_ACCOUNT_AUTH_FILEPATH = "tests/example_accounts/updated_accounts/test_update_k8s_vanilla_account_service_account_auth.py"
DSL_VMWARE_UPDATE_ACCOUNT_FILEPATH = (
    "tests/example_accounts/updated_accounts/test_update_vmware_account.py"
)
DSL_NDB_UPDATE_ACCOUNT_FILEPATH = (
    "tests/example_accounts/updated_accounts/update_ndb_account.py"
)
DSL_CREDENTIAL_PROVIDER_UPDATE_ACCOUNT_FILEPATH = (
    "tests/example_accounts/updated_accounts/test_update_credential_provider_account.py"
)


class TestAccountCommands:
    def setup_method(self):
        """Method to instantiate to created_bp_list and reset context"""

        # Resetting context
        ContextObj = get_context()
        ContextObj.reset_configuration()

        # Resetting metadata object
        reset_metadata_obj()

        self.created_account_list = []
        self.created_provider_list = []

    def teardown_method(self):
        """Method to delete creates accounts and apps during tests"""

        client = get_api_client()

        # Resetting metadata object
        reset_metadata_obj()

        for account_uuid in self.created_account_list:
            LOG.info("Deleting Account with UUID: {}".format(account_uuid))
            _, err = client.account.delete(account_uuid)
            assert err == None

        for provider_uuid in self.created_provider_list:
            LOG.info("Deleting Provider with UUID: {}".format(provider_uuid))
            _, err = client.provider.delete(provider_uuid)
            assert err == None

        self.created_account_list = []
        self.created_provider_list = []

    @pytest.mark.parametrize(
        "account_file_path, json_file_path",
        [
            (DSL_AHV_ACCOUNT_FILEPATH, AHV_ACCOUNT_JSON_FILEPATH),
            (DSL_AWS_ACCOUNT_FILEPATH, AWS_ACCOUNT_JSON_FILEPATH),
            (DSL_AWS_C2S_ACCOUNT_FILEPATH, AWS_C2S_ACCOUNT_JSON_FILEPATH),
            (DSL_AZURE_ACCOUNT_FILEPATH, AZURE_ACCOUNT_JSON_FILEPATH),
            (DSL_GCP_ACCOUNT_FILEPATH, GCP_ACCOUNT_JSON_FILEPATH),
            (
                DSL_K8S_VANILLA_ACCOUNT_BASIC_AUTH_FILEPATH,
                K8S_VANILLA_ACCOUNT_JSON_BASIC_AUTH_FILEPATH,
            ),
            (
                DSL_K8S_VANILLA_ACCOUNT_CA_CERTIFICATE_AUTH_FILEPATH,
                K8S_VANILLA_ACCOUNT_JSON_CA_CERTIFICATE_AUTH_FILEPATH,
            ),
            (
                DSL_K8S_VANILLA_ACCOUNT_CLIENT_CERTIFICATE_AUTH_FILEPATH,
                K8S_VANILLA_ACCOUNT_JSON_CLIENT_CERTIFICATE_AUTH_FILEPATH,
            ),
            (
                DSL_K8S_VANILLA_ACCOUNT_SERVICE_ACCOUNT_AUTH_FILEPATH,
                K8S_VANILLA_ACCOUNT_JSON_SERVICE_ACCOUNT_AUTH_FILEPATH,
            ),
            (DSL_VMWARE_ACCOUNT_FILEPATH, VMWARE_ACCOUNT_JSON_FILEPATH),
            (DSL_NDB_ACCOUNT_FILEPATH, NDB_ACCOUNT_JSON_FILEPATH),
            (
                DSL_CREDENTIAL_PROVIDER_ACCOUNT_FILEPATH,
                CREDENTIAL_PROVIDER_ACCOUNT_JSON_FILEPATH,
            ),
        ],
    )
    def test_compile_account(self, account_file_path, json_file_path):
        runner = CliRunner()
        LOG.info("Compiling Account file at {}".format(account_file_path))
        result = runner.invoke(
            cli, ["compile", "account", "--file={}".format(account_file_path)]
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
            pytest.fail("ACCOUNT compile command failed")

        with open(json_file_path) as f:
            known_json = json.load(f)

        compiled_payload = json.loads(result.output)
        compiled_payload["metadata"]["uuid"] = ""
        if account_file_path == DSL_VMWARE_ACCOUNT_FILEPATH:
            price_item_list = compiled_payload["spec"]["resources"]["price_items"]
            for price_item in price_item_list:
                price_item["uuid"] = ""

        if account_file_path in [
            DSL_NDB_ACCOUNT_FILEPATH,
            DSL_CREDENTIAL_PROVIDER_ACCOUNT_FILEPATH,
        ]:
            compiled_payload["spec"]["resources"]["data"]["provider_reference"][
                "uuid"
            ] = ""
            variable_list = compiled_payload["spec"]["resources"]["data"][
                "variable_list"
            ]

            for variable in variable_list:
                variable["uuid"] = ""

        if account_file_path == DSL_NDB_ACCOUNT_FILEPATH:
            compiled_payload["spec"]["resources"]["parent_reference"]["uuid"] = ""

        elif account_file_path == DSL_AHV_ACCOUNT_FILEPATH:
            known_json["spec"]["resources"]["data"]["server"] = compiled_payload[
                "spec"
            ]["resources"]["data"]["server"]

        assert compiled_payload == known_json
        LOG.info("Success")

    @pytest.mark.parametrize(
        "account_file_path, update_account_file_path",
        [
            (DSL_AHV_ACCOUNT_FILEPATH, DSL_AHV_UPDATE_ACCOUNT_FILEPATH),
            (DSL_AWS_ACCOUNT_FILEPATH, DSL_AWS_UPDATE_ACCOUNT_FILEPATH),
            (DSL_AWS_C2S_ACCOUNT_FILEPATH, DSL_AWS_C2S_UPDATE_ACCOUNT_FILEPATH),
            (DSL_AZURE_ACCOUNT_FILEPATH, DSL_AZURE_UPDATE_ACCOUNT_FILEPATH),
            (DSL_GCP_ACCOUNT_FILEPATH, DSL_GCP_UPDATE_ACCOUNT_FILEPATH),
            (
                DSL_K8S_VANILLA_ACCOUNT_BASIC_AUTH_FILEPATH,
                DSL_K8S_VANILLA_UPDATE_ACCOUNT_BASIC_AUTH_FILEPATH,
            ),
            (
                DSL_K8S_VANILLA_ACCOUNT_CA_CERTIFICATE_AUTH_FILEPATH,
                DSL_K8S_VANILLA_UPDATE_ACCOUNT_CA_CERTIFICATE_AUTH_FILEPATH,
            ),
            (
                DSL_K8S_VANILLA_ACCOUNT_CLIENT_CERTIFICATE_AUTH_FILEPATH,
                DSL_K8S_VANILLA_UPDATE_ACCOUNT_CLIENT_CERTIFICATE_AUTH_FILEPATH,
            ),
            (
                DSL_K8S_VANILLA_ACCOUNT_SERVICE_ACCOUNT_AUTH_FILEPATH,
                DSL_K8S_VANILLA_UPDATE_ACCOUNT_SERVICE_ACCOUNT_AUTH_FILEPATH,
            ),
            (DSL_VMWARE_ACCOUNT_FILEPATH, DSL_VMWARE_UPDATE_ACCOUNT_FILEPATH),
            (
                DSL_CREDENTIAL_PROVIDER_ACCOUNT_FILEPATH,
                DSL_CREDENTIAL_PROVIDER_UPDATE_ACCOUNT_FILEPATH,
            ),
        ],
    )
    def test_dsl_account_create(self, account_file_path, update_account_file_path):

        client = get_api_client()

        runner = CliRunner()
        self.created_dsl_account_name = "Test_Account_DSL_{}".format(
            str(uuid.uuid4())[-10:]
        )
        LOG.info("Creating Account {}".format(self.created_dsl_account_name))
        result = runner.invoke(
            cli,
            [
                "create",
                "account",
                "--file={}".format(account_file_path),
                "--name={}".format(self.created_dsl_account_name),
            ],
        )

        params = {"filter": "name=={}".format(self.created_dsl_account_name)}
        res, err = client.account.list(params=params)
        response = res.json()

        if err:
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
            pytest.fail("ACCOUNT creation from python file failed")

        account_uuid = (
            response.get("entities", [{}])[0].get("metadata", {}).get("uuid", "")
        )
        self.created_account_list.append(account_uuid)

        if account_file_path == DSL_CREDENTIAL_PROVIDER_ACCOUNT_FILEPATH:

            provider_uuid = (
                response.get("entities", [{}])[0]
                .get("status", {})
                .get("resources", {})
                .get("data", {})
                .get("provider_reference", {})
                .get("uuid", "")
            )
            self.created_provider_list.append(provider_uuid)

        account_status = (
            response.get("entities", [{}])[0]
            .get("status", {})
            .get("resources", {})
            .get("state", "")
        )

        assert (
            (account_status == "ACTIVE")
            or (account_status == "VERIFIED")
            or (account_status == "DRAFT")
        )

        LOG.info("Account Creation Successfull")

        self._test_account_update(update_account_file_path)

    def _test_account_update(self, update_account_file_path):

        runner = CliRunner()
        client = get_api_client()
        self.updated_account_name = self.created_dsl_account_name + "_updated"
        LOG.info("Updating Account {}".format(self.created_dsl_account_name))
        result = runner.invoke(
            cli,
            [
                "update",
                "account",
                self.created_dsl_account_name,
                "--file={}".format(update_account_file_path),
                "--updated-name={}".format(self.updated_account_name),
            ],
        )

        params = {"filter": "name=={}".format(self.updated_account_name)}
        res, err = client.account.list(params=params)
        response = res.json()

        if err:
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
            pytest.fail("ACCOUNT creation from python file failed")

        if update_account_file_path == DSL_CREDENTIAL_PROVIDER_UPDATE_ACCOUNT_FILEPATH:

            provider_uuid = (
                response.get("entities", [{}])[0]
                .get("status", {})
                .get("resources", {})
                .get("data", {})
                .get("provider_reference", {})
                .get("uuid", "")
            )
            self.created_provider_list.append(provider_uuid)

        if update_account_file_path == DSL_NDB_UPDATE_ACCOUNT_FILEPATH:
            account_status = response.get("status", {})
            account_status = account_status.get("resources", {}).get("state", "DRAFT")
        else:
            account_status = (
                response.get("entities", [{}])[0]
                .get("status", {})
                .get("resources", {})
                .get("state", "")
            )

        assert (
            (account_status == "ACTIVE")
            or (account_status == "VERIFIED")
            or (account_status == "DRAFT")
        )

        LOG.info("Account Updation Successfull")

    def test_ndb_account_create(self):

        client = get_api_client()
        self.created_dsl_account_name = "Test_Account_NDB_{}".format(
            str(uuid.uuid4())[-10:]
        )
        account_file_path = DSL_NDB_ACCOUNT_FILEPATH

        LOG.info("Creating Account {}".format(self.created_dsl_account_name))
        account_data = create_account_from_dsl(
            client, account_file_path, name=self.created_dsl_account_name
        )

        account_state = account_data["state"]

        self.created_account_list.append(account_data["uuid"])

        assert (
            (account_state == "ACTIVE")
            or (account_state == "VERIFIED")
            or (account_state == "DRAFT")
        )

        LOG.info("Account Creation Successfull")

        self._test_account_update(DSL_NDB_UPDATE_ACCOUNT_FILEPATH)


if __name__ == "__main__":
    tester = TestAccountCommands()
