import json

import pytest

from tests.existing_vm_example.test_existing_vm_bp import (
    ExistingVMBlueprint as Blueprint,
)

# from tests.next_demo.test_next_demo import NextDslBlueprint as Blueprint

from calm.dsl.cli import get_api_client, launch_blueprint_simple


# Import all api utils from cli


def test_bp_list():

    client = get_api_client()

    params = {"length": 20, "offset": 0}
    res, err = client.blueprint.list(params=params)

    if not err:
        print(">> Blueprint List >>")
        print(json.dumps(res.json(), indent=4, separators=(",", ": ")))
        assert res.ok is True
    else:
        pytest.fail("[{}] - {}".format(err["code"], err["error"]))


@pytest.mark.slow
def test_next_demo_bp_upload(Blueprint=Blueprint):

    client = get_api_client()

    # seek and destroy
    params = {"filter": "name=={};state!=DELETED".format(Blueprint)}
    res, err = client.blueprint.list(params=params)
    if err:
        pytest.fail("[{}] - {}".format(err["code"], err["error"]))

    response = res.json()
    entities = response.get("entities", None)
    if entities:
        if len(entities) != 1:
            pytest.fail("More than one blueprint found - {}".format(entities))

        print(">> {} found >>".format(Blueprint))
        uuid = entities[0]["metadata"]["uuid"]

        res, err = client.blueprint.delete(uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        print(">> {} deleted >>".format(Blueprint))

    else:
        print(">> {} not found >>".format(Blueprint))

    # upload
    bp_name = Blueprint.__name__
    bp_desc = Blueprint.__doc__
    bp_resources = json.loads(Blueprint.json_dumps())
    res, err = client.blueprint.upload_with_secrets(bp_name, bp_desc, bp_resources)

    if not err:
        print(">> {} uploaded with creds >>".format(Blueprint))
        print(json.dumps(res.json(), indent=4, separators=(",", ": ")))
        assert res.ok is True
    else:
        pytest.fail("[{}] - {}".format(err["code"], err["error"]))

    bp = res.json()
    bp_state = bp["status"]["state"]
    print(">> Blueprint state: {}".format(bp_state))
    assert bp_state == "ACTIVE"


@pytest.mark.slow
def test_next_demo_bp_launch(Blueprint=Blueprint):

    client = get_api_client()
    launch_blueprint_simple(client, str(Blueprint), patch_editables=False)


def test_session_close():

    client = get_api_client()
    client.connection.close()


def main():
    test_bp_list()
    test_next_demo_bp_upload()
    test_next_demo_bp_launch()
    test_session_close()


if __name__ == "__main__":
    main()
