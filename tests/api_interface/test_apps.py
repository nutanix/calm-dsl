import pytest
import json
import uuid
import time

from calm.dsl.cli.main import get_api_client
from calm.dsl.cli.bps import launch_blueprint_simple
from calm.dsl.log import get_logging_handle
from calm.dsl.cli.constants import RUNLOG, APPLICATION
from tests.api_interface.entity_spec.existing_vm_bp import (
    ExistingVMBlueprint as Blueprint,
)

LOG = get_logging_handle(__name__)


class TestApps:
    def test_apps_list(self):

        client = get_api_client()

        params = {"length": 20, "offset": 0}
        LOG.info("Invoking list api call on apps")
        res, err = client.application.list(params=params)

        if not err:
            assert res.ok is True
            LOG.info("Success")
            LOG.debug("Response: {}".format(res.json()))
        else:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

    @pytest.mark.slow
    def test_apps_api(self):

        client = get_api_client()

        # uploading the blueprint
        bp_name = "test_bp_" + str(uuid.uuid4())[-10:]
        LOG.info("Creating blueprint {}".format(bp_name))
        bp_desc = Blueprint.__doc__
        bp_resources = json.loads(Blueprint.json_dumps())
        res, err = client.blueprint.upload_with_secrets(bp_name, bp_desc, bp_resources)

        if not err:
            LOG.info("{} uploaded with creds".format(Blueprint))
            LOG.debug("Response: {}".format(res.json()))
            assert res.ok is True
        else:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        bp = res.json()
        bp_state = bp["status"]["state"]
        bp_uuid = bp["metadata"]["uuid"]
        assert bp_state == "ACTIVE"
        assert bp_name == bp["spec"]["name"]
        assert bp_name == bp["metadata"]["name"]
        assert bp_name == bp["metadata"]["name"]

        # launching the blueprint
        LOG.info("Launching blueprint {}".format(bp_name))
        app_name = "test_bp_api{}".format(str(uuid.uuid4())[-10:])

        try:
            launch_blueprint_simple(blueprint_name=bp_name, app_name=app_name)
        except Exception as exp:
            pytest.fail(exp)

        params = {"filter": "name=={}".format(app_name)}
        res, err = client.application.list(params=params)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        response = res.json()
        entities = response.get("entities", None)
        app = None
        if entities:
            if len(entities) != 1:
                raise Exception("More than one blueprint found - {}".format(entities))
            app = entities[0]

        else:
            raise Exception("Application not found")

        app_uuid = app["metadata"]["uuid"]
        # poll for app create action to be happened correctly
        maxWait = 5 * 60
        count = 0
        poll_interval = 10
        while count < maxWait:

            res, err = client.application.read(app_uuid)
            if err:
                pytest.fail(err)

            res = res.json()
            state = res["status"]["state"]
            if state == APPLICATION.STATES.PROVISIONING:
                LOG.info("App {} is in provisioning state".format(app_name))

            elif state == APPLICATION.STATES.ERROR:
                pytest.fail("App creation failed. App went to error state")
                break

            elif state == APPLICATION.STATES.RUNNING:
                LOG.info("App {} is in running state".format(app_name))
                break

            else:
                LOG.info("application state: {}".format(state))
                break

            count += poll_interval
            time.sleep(poll_interval)

        res, err = client.application.read(app_uuid)
        if err:
            pytest.fail(err)

        app = res.json()
        app_spec = app["spec"]
        app_uuid = app["metadata"]["uuid"]

        actions = ["stop", "start"]
        # soft_delete and delete actions are unable to run using run_action api

        LOG.info("Performing actions on application {}".format(app_name))
        for action_name in actions:
            calm_action_name = "action_" + action_name.lower()
            LOG.info(
                "Running action {} on application {}".format(action_name, app_name)
            )
            action = next(
                action
                for action in app_spec["resources"]["action_list"]
                if action["name"] == calm_action_name or action["name"] == action_name
            )
            if not action:
                pytest.fail("No action found matching name {}".format(action_name))

            action_id = action["uuid"]

            app.pop("status", None)
            app["spec"] = {
                "args": [],
                "target_kind": "Application",
                "target_uuid": app_uuid,
            }
            res, err = client.application.run_action(app_uuid, action_id, app)
            if err:
                pytest.fail("[{}] - {}".format(err["code"], err["error"]))

            response = res.json()
            runlog_uuid = response["status"]["runlog_uuid"]

            url = client.application.ITEM.format(app_uuid) + "/app_runlogs/list"
            payload = {"filter": "root_reference=={}".format(runlog_uuid)}

            maxWait = 5 * 60
            count = 0
            poll_interval = 10
            while count < maxWait:
                # call status api
                res, err = client.application.poll_action_run(url, payload)
                if err:
                    raise Exception("[{}] - {}".format(err["code"], err["error"]))
                response = res.json()
                entities = response["entities"]
                wait_over = False
                if len(entities):
                    sorted_entities = sorted(
                        entities, key=lambda x: int(x["metadata"]["creation_time"])
                    )
                    for runlog in sorted_entities:
                        state = runlog["status"]["state"]
                        if state in RUNLOG.FAILURE_STATES:
                            pytest.fail("action {} failed".format(action_name))
                            break
                        elif state not in RUNLOG.TERMINAL_STATES:
                            LOG.info("Action {} is in process".format(action_name))
                            break
                        else:
                            wait_over = True

                if wait_over:
                    LOG.info("Action {} completed".format(action_name))
                    break

                count += poll_interval
                time.sleep(poll_interval)

            if count >= maxWait:
                pytest.fail(
                    "action {} is not completed in 5 minutes".format(action_name)
                )

        LOG.info("Deleting application {}".format(app_name))
        res, err = client.application.delete(app_uuid)
        if err:
            pytest.fail(err)

        # poll for app delete action to be happened correctly
        LOG.info("Polling for delete operation on app {}".format(app_name))
        maxWait = 5 * 60
        count = 0
        poll_interval = 10
        while count < maxWait:

            res, err = client.application.read(app_uuid)
            if err:
                pytest.fail(err)

            res = res.json()
            state = res["status"]["state"]
            if state == APPLICATION.STATES.RUNNING:
                LOG.info("APP {} is in running state".format(app_name))

            elif state == APPLICATION.STATES.DELETING:
                LOG.info("APP {} is in deleting state".format(app_name))

            elif state == APPLICATION.STATES.ERROR:
                pytest.fail("App {} creation failed".format(app_name))

            elif state == APPLICATION.STATES.DELETED:
                LOG.info("App {} is deleted".format(app_name))
                break

            else:
                LOG.info("Application state: {}".format(state))

            count += poll_interval
            time.sleep(poll_interval)

        LOG.info("Deleting blueprint of application {}".format(app_name))
        res, err = client.blueprint.delete(bp_uuid)
        if err:
            pytest.fail(err)

        else:
            LOG.info("Blueprint {} deleted".format(bp_name))
