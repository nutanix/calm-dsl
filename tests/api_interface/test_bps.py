import pytest
import json
import uuid

from calm.dsl.cli.main import get_api_client
from calm.dsl.cli.bps import launch_blueprint_simple
from tests.api_interface.entity_spec.existing_vm_bp import (
    ExistingVMBlueprint as Blueprint,
)


class TestBps:
    def test_bps_list(self):

        client = get_api_client()

        params = {"length": 20, "offset": 0}
        res, err = client.blueprint.list(params=params)

        if not err:
            print("\n>> Blueprint list call successful>>")
            assert res.ok is True
        else:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

    @pytest.mark.slow
    def test_upload_and_launch_bp(self):

        client = get_api_client()
        bp_name = "test_ask_" + str(uuid.uuid4())[-10:]

        params = {"filter": "name=={};state!=DELETED".format(bp_name)}
        res, err = client.blueprint.list(params=params)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        entities = res.get("entities", None)
        print("\nSearching and deleting existing blueprint having same name")
        if entities:
            if len(entities) != 1:
                pytest.fail("More than one blueprint found - {}".format(entities))

            print(">> {} found >>".format(Blueprint))
            bp_uuid = entities[0]["metadata"]["uuid"]

            res, err = client.blueprint.delete(bp_uuid)
            if err:
                pytest.fail("[{}] - {}".format(err["code"], err["error"]))

            print(">> {} deleted >>".format(Blueprint))

        else:
            print(">> {} not found >>".format(Blueprint))

        # uploading the blueprint
        print("\n>>Creating the blueprint {}".format(bp_name))
        bp_desc = Blueprint.__doc__
        bp_resources = json.loads(Blueprint.json_dumps())
        res, err = client.blueprint.upload_with_secrets(bp_name, bp_desc, bp_resources)

        if not err:
            print(">> {} uploaded with creds >>".format(Blueprint))
            assert res.ok is True
        else:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        bp = res.json()
        bp_state = bp["status"]["state"]
        bp_uuid = bp["metadata"]["uuid"]
        print(">> Blueprint state: {}".format(bp_state))
        assert bp_state == "ACTIVE"
        assert bp_name == bp["spec"]["name"]
        assert bp_name == bp["metadata"]["name"]
        assert bp_name == bp["metadata"]["name"]

        # launching the blueprint
        print("\n>>Launching the blueprint")
        app_name = "test_bp_api{}".format(str(uuid.uuid4())[-10:])

        try:
            launch_blueprint_simple(client, blueprint_name=bp_name, app_name=app_name)
        except Exception as exp:
            pytest.fail(exp)

    @pytest.mark.slow
    def test_bp_crud(self):

        client = get_api_client()
        bp_name = "test_ask_" + str(uuid.uuid4())[-10:]

        bp_desc = Blueprint.__doc__
        bp_resources = json.loads(Blueprint.json_dumps())

        print("\n>>Uploading blueprint")
        res, err = client.blueprint.upload_with_secrets(bp_name, bp_desc, bp_resources)

        if not err:
            print(">> {} uploaded with creds >>".format(bp_name))
            assert res.ok is True
        else:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        bp = res.json()
        bp_state = bp["status"]["state"]
        bp_uuid = bp["metadata"]["uuid"]
        print(">> Blueprint state: {}".format(bp_state))
        assert bp_state == "ACTIVE"
        assert bp_name == bp["spec"]["name"]
        assert bp_name == bp["metadata"]["name"]
        assert bp_name == bp["metadata"]["name"]

        # reading the bluprint using get call
        print("\n>>Reading blueprint")
        res, err = client.blueprint.read(bp_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        else:
            assert res.ok is True
            res = res.json()
            assert bp_name == res["spec"]["name"]
            assert bp_name == res["metadata"]["name"]
            assert bp_name == res["metadata"]["name"]
            print(">> Get call to blueprint is successful >>")

        # deleting the blueprint
        print("\n>>Deleting blueprint")
        res, err = client.blueprint.delete(bp_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        else:
            assert res.ok is True
            res = res.json()
            print("API Response: {}".format(res["description"]))
            print(">> Delete call to blueprint is successful >>")
