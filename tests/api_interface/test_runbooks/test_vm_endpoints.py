import pytest
import os
import json
from distutils.version import LooseVersion as LV

from calm.dsl.store import Version
from calm.dsl.cli.main import get_api_client
from calm.dsl.cli.constants import ENDPOINT
from tests.api_interface.test_runbooks.utils import (
    read_test_config,
    change_uuids,
    add_account_uuid,
    add_vm_reference,
)
from calm.dsl.builtins import read_local_file
from calm.dsl.log import get_logging_handle


LOG = get_logging_handle(__name__)

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
PROJECT = DSL_CONFIG["PROJECTS"]["PROJECT1"]
PROJECT_NAME = PROJECT["NAME"]


LinuxVMStaticAHVEpPayload = read_test_config(
    file_name="linux_vm_static_ahv_ep_payload.json"
)
LinuxVMDynamicAHVEpPayload = read_test_config(
    file_name="linux_vm_dynamic_ahv_ep_payload.json"
)
WindowsVMStaticAHVEpPayload = read_test_config(
    file_name="windows_vm_static_ahv_ep_payload.json"
)
WindowsVMDynamicAHVEpPayload = read_test_config(
    file_name="windows_vm_dynamic_ahv_ep_payload.json"
)

# calm_version
CALM_VERSION = Version.get_version("Calm")


@pytest.mark.skipif(
    LV(CALM_VERSION) < LV("3.2.0"),
    reason="Tests are for env changes introduced in 3.2.0",
)
class TestVMEndpoints:
    @pytest.mark.runbook
    @pytest.mark.regression
    @pytest.mark.parametrize(
        "EndpointPayload",
        [
            WindowsVMStaticAHVEpPayload,
            LinuxVMStaticAHVEpPayload,
            LinuxVMDynamicAHVEpPayload,
            WindowsVMDynamicAHVEpPayload,
        ],
    )
    def test_vm_endpoint_static_crud(self, EndpointPayload):
        """Endpoint for VM crud"""
        client = get_api_client()
        vm_references = EndpointPayload["spec"]["resources"]["attrs"].get(
            "vm_references", []
        )

        add_vm_reference(vm_references, PROJECT_NAME)
        endpoint = change_uuids(EndpointPayload, {})
        res, err = add_account_uuid(EndpointPayload)

        if not res:
            pytest.fail(err)

        # Endpoint Create
        print(">> Creating endpoint")
        res, err = client.endpoint.create(endpoint)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        ep = res.json()
        ep_state = ep["status"]["state"]
        ep_uuid = ep["metadata"]["uuid"]
        ep_name = ep["spec"]["name"]
        print(">> Endpoint state: {}".format(ep_state))
        assert ep_state == "ACTIVE"

        # Endpoint Read
        print(">> Reading endpoint (uuid={})".format(ep_uuid))
        res, err = client.endpoint.read(id=ep_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        ep = res.json()
        ep_state = ep["status"]["state"]
        assert ep_uuid == ep["metadata"]["uuid"]
        assert ep_state == "ACTIVE"
        assert ep_name == ep["spec"]["name"]

        # Endpoint Update
        ep_type = ep["spec"]["resources"]["type"]
        ep_value_type = ep["spec"]["resources"]["value_type"]
        del ep["status"]
        if ep_type != ENDPOINT.TYPES.HTTP and ep_value_type == ENDPOINT.VALUE_TYPES.VM:
            ep["spec"]["resources"]["attrs"]["values"] = [
                "f2fa6e06-5684-4089-9c73-f84f19afc15e",
                "b78f1695-bb14-4de1-be87-dd17012f913c",
            ]
        else:
            pytest.fail("Invalid type {} of the endpoint".format(ep_type))

        print(">> Updating endpoint (uuid={})".format(ep_uuid))
        res, err = client.endpoint.update(ep_uuid, ep)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        ep = res.json()
        ep_state = ep["status"]["state"]
        ep_value_type = ep["status"]["resources"]["value_type"]
        print(">> Endpoint state: {}".format(ep_state))
        assert ep_state == "ACTIVE"
        if ep_type != ENDPOINT.TYPES.HTTP and ep_value_type == ENDPOINT.VALUE_TYPES.VM:
            assert (
                "f2fa6e06-5684-4089-9c73-f84f19afc15e"
                in ep["spec"]["resources"]["attrs"]["values"]
            )
            assert (
                "b78f1695-bb14-4de1-be87-dd17012f913c"
                in ep["spec"]["resources"]["attrs"]["values"]
            )
            assert len(ep["spec"]["resources"]["attrs"]["values"]) == 2
        else:
            pytest.fail("Invalid type {} of the endpoint".format(ep_type))

        # download the endpoint
        print(">> Downloading endpoint (uuid={})".format(ep_uuid))
        file_path = client.endpoint.export_file(ep_uuid, passphrase="test_passphrase")

        project_list_params = {"filter": "name=={}".format("default")}
        res, err = client.project.list(params=project_list_params)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        response = res.json()
        default_project_uuid = response["entities"][0]["metadata"]["uuid"]
        print(">> Default project uuid: {}".format(default_project_uuid))

        # upload the endpoint
        print(">> Uploading endpoint (uuid={})".format(ep_uuid))
        res, err = client.endpoint.import_file(
            file_path,
            ep_name + "-uploaded",
            default_project_uuid,
            passphrase="test_passphrase",
        )
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        uploaded_ep = res.json()
        uploaded_ep_state = uploaded_ep["status"]["state"]
        uploaded_ep_uuid = uploaded_ep["metadata"]["uuid"]
        assert uploaded_ep_state == "ACTIVE"

        # delete uploaded endpoint
        print(">> Deleting uploaded endpoint (uuid={})".format(uploaded_ep_uuid))
        _, err = client.endpoint.delete(uploaded_ep_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        else:
            print("uploaded endpoint deleted")

        # delete downloaded file
        os.remove(file_path)

        # delete the endpoint
        print(">> Deleting endpoint (uuid={})".format(ep_uuid))
        _, err = client.endpoint.delete(ep_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        else:
            print("endpoint {} deleted".format(ep_name))
        res, err = client.endpoint.read(id=ep_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        ep = res.json()
        ep_state = ep["status"]["state"]
        assert ep_state == "DELETED"

    @pytest.mark.parametrize(
        "EndpointPayload",
        [WindowsVMDynamicAHVEpPayload],
    )
    def test_vm_endpoint_dynamic_crud(self, EndpointPayload):
        """Endpoint for VM crud"""
        client = get_api_client()
        endpoint = change_uuids(EndpointPayload, {})
        res, err = add_account_uuid(EndpointPayload)
        if not res:
            pytest.fail(err)

        # Endpoint Create
        print(">> Creating endpoint")
        res, err = client.endpoint.create(endpoint)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        ep = res.json()
        ep_state = ep["status"]["state"]
        ep_uuid = ep["metadata"]["uuid"]
        ep_name = ep["spec"]["name"]
        print(">> Endpoint state: {}".format(ep_state))
        assert ep_state == "ACTIVE"

        # Endpoint Read
        print(">> Reading endpoint (uuid={})".format(ep_uuid))
        res, err = client.endpoint.read(id=ep_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        ep = res.json()
        ep_state = ep["status"]["state"]
        ep_filter_type = ep["status"]["resources"]["attrs"]["filter_type"]
        assert ep_uuid == ep["metadata"]["uuid"]
        assert ep_state == "ACTIVE"
        assert ep_name == ep["spec"]["name"]
        assert ep_filter_type == "dynamic"

        # Endpoint Update
        ep_type = ep["spec"]["resources"]["type"]
        ep_value_type = ep["spec"]["resources"]["value_type"]
        ep_filter_type = ep["spec"]["resources"]["attrs"]["filter_type"]
        del ep["status"]
        if (
            ep_type != ENDPOINT.TYPES.HTTP
            and ep_value_type == ENDPOINT.VALUE_TYPES.VM
            and ep_filter_type == "dynamic"
        ):
            ep["spec"]["resources"]["attrs"]["filter"] = "power_state==on"
        else:
            pytest.fail("Invalid type {} of the endpoint".format(ep_type))

        print(">> Updating endpoint (uuid={})".format(ep_uuid))
        res, err = client.endpoint.update(ep_uuid, ep)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        ep = res.json()
        ep_state = ep["status"]["state"]
        ep_value_type = ep["status"]["resources"]["value_type"]
        print(">> Endpoint state: {}".format(ep_state))
        assert ep_state == "ACTIVE"
        if (
            ep_type != ENDPOINT.TYPES.HTTP
            and ep_value_type == ENDPOINT.VALUE_TYPES.VM
            and ep_filter_type == "dynamic"
        ):
            assert "power_state==on" in ep["spec"]["resources"]["attrs"]["filter"]
        else:
            pytest.fail("Invalid type {} of the endpoint".format(ep_type))

        # download the endpoint
        print(">> Downloading endpoint (uuid={})".format(ep_uuid))
        file_path = client.endpoint.export_file(ep_uuid, passphrase="test_passphrase")

        project_list_params = {"filter": "name=={}".format("default")}
        res, err = client.project.list(params=project_list_params)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        response = res.json()
        default_project_uuid = response["entities"][0]["metadata"]["uuid"]
        print(">> Default project uuid: {}".format(default_project_uuid))

        # upload the endpoint
        print(">> Uploading endpoint (uuid={})".format(ep_uuid))
        res, err = client.endpoint.import_file(
            file_path,
            ep_name + "-uploaded",
            default_project_uuid,
            passphrase="test_passphrase",
        )
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        uploaded_ep = res.json()
        uploaded_ep_state = uploaded_ep["status"]["state"]
        uploaded_ep_uuid = uploaded_ep["metadata"]["uuid"]
        assert uploaded_ep_state == "ACTIVE"

        # delete uploaded endpoint
        print(">> Deleting uploaded endpoint (uuid={})".format(uploaded_ep_uuid))
        _, err = client.endpoint.delete(uploaded_ep_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        else:
            print("uploaded endpoint deleted")

        # delete downloaded file
        os.remove(file_path)

        # delete the endpoint
        print(">> Deleting endpoint (uuid={})".format(ep_uuid))
        _, err = client.endpoint.delete(ep_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        else:
            print("endpoint {} deleted".format(ep_name))
        res, err = client.endpoint.read(id=ep_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        ep = res.json()
        ep_state = ep["status"]["state"]
        assert ep_state == "DELETED"
