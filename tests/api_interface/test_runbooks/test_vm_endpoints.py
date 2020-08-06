import pytest
import os

from calm.dsl.cli.main import get_api_client
from calm.dsl.cli.constants import ENDPOINT
from utils import read_test_config

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


class TestVMEndpoints:
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
        # endpoint = change_uuids(EndpointPayload, {})
        endpoint = EndpointPayload

        # Endpoint Create
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
        file_path = client.endpoint.export_file(ep_uuid, passphrase="test_passphrase")

        # upload the endpoint
        res, err = client.endpoint.import_file(
            file_path,
            ep_name + "-uploaded",
            ep["metadata"].get("project_reference", {}).get("uuid", ""),
            passphrase="test_passphrase",
        )
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        uploaded_ep = res.json()
        uploaded_ep_state = uploaded_ep["status"]["state"]
        uploaded_ep_uuid = uploaded_ep["metadata"]["uuid"]
        assert uploaded_ep_state == "ACTIVE"

        # delete uploaded endpoint
        _, err = client.endpoint.delete(uploaded_ep_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        else:
            print("uploaded endpoint deleted")

        # delete downloaded file
        os.remove(file_path)

        # delete the endpoint
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
        "EndpointPayload", [WindowsVMDynamicAHVEpPayload],
    )
    def test_vm_endpoint_dynamic_crud(self, EndpointPayload):
        """Endpoint for VM crud"""
        client = get_api_client()
        # endpoint = change_uuids(EndpointPayload, {})
        endpoint = EndpointPayload

        # Endpoint Create
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
        file_path = client.endpoint.export_file(ep_uuid, passphrase="test_passphrase")

        # upload the endpoint
        res, err = client.endpoint.import_file(
            file_path,
            ep_name + "-uploaded",
            ep["metadata"].get("project_reference", {}).get("uuid", ""),
            passphrase="test_passphrase",
        )
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        uploaded_ep = res.json()
        uploaded_ep_state = uploaded_ep["status"]["state"]
        uploaded_ep_uuid = uploaded_ep["metadata"]["uuid"]
        assert uploaded_ep_state == "ACTIVE"

        # delete uploaded endpoint
        _, err = client.endpoint.delete(uploaded_ep_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        else:
            print("uploaded endpoint deleted")

        # delete downloaded file
        os.remove(file_path)

        # delete the endpoint
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
