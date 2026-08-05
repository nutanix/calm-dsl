import uuid
import time
import json
import traceback
import pytest
from distutils.version import LooseVersion as LV
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.api import get_api_client
from calm.dsl.store import Version
from calm.dsl.cli.constants import APPLICATION, RUNLOG
from calm.dsl.tools import make_file_dir
from calm.dsl.log import get_logging_handle
from calm.dsl.builtins import read_local_file
from calm.dsl.constants import CONFIG_TYPE
from tests.utils import Application as ApplicationHelper

LOG = get_logging_handle(__name__)

CALM_VERSION = Version.get_version("Calm")

NORMAL_DSL_BP_FILEPATH = "tests/vm_recovery_point/normal_bp.py"
VRC_DSL_BP_FILEPATH = "tests/vm_recovery_point/blueprint.py"
LOCAL_RP_NAME_PATH = "tests/vm_recovery_point/.local/vm_rp_name"
DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))

AHV_SNAPSHOT_PROJECTS = DSL_CONFIG.get("AHV_SNAPSHOT_PROJECTS", {})
PROJECT = AHV_SNAPSHOT_PROJECTS.get("PROJECT1") or {}

ENV_NAME = (PROJECT.get("ENVIRONMENTS") or [{}])[0].get("NAME", "")
ACC_UUID = (PROJECT.get("ACCOUNTS", {}).get("NUTANIX_PC") or [{}])[0].get("UUID", "")

_SNAPSHOT_POLICY = PROJECT.get("SNAPSHOT_POLICY", [{}])[0] if PROJECT else {}
SNAPSHOT_POLICY_NAME = _SNAPSHOT_POLICY.get("NAME", "")
LOCAL_RULE_NAME = _SNAPSHOT_POLICY.get("RULE", "")
# Path where the dynamically generated launch_params file is written
SNAPSHOT_LAUNCH_PARAMS_PATH = "tests/vm_recovery_point/.local/snapshot_launch_params.py"

# Name of the snapshot action auto-generated from the "s1" SnapshotConfig in normal_bp.py
SNAPSHOT_ACTION_NAME = "Snapshot_s1"


@pytest.mark.skipif(
    not PROJECT,
    reason="Snapshot Project is not present on the setup or is not configured correctly",
)
@pytest.mark.slow
class TestVmRecoveryPointBp:
    app_helper = ApplicationHelper()

    vrp_name = ""
    vrp_uuid = ""

    def setup_method(self):
        """Method to instantiate to created_bp_list and created_app_list"""

        # TODO add deletion of vms also.
        self.created_bp_list = []
        self.created_app_list = []

        if not self.vrp_name:
            vrp_data = self._create_vm_recovery_point()
            self.vrp_name = vrp_data["name"]
            self.vrp_uuid = vrp_data["uuid"]

            # Writing vm_ip to local directory file
            LOG.info(
                "Writing vrp name {} to file '{}'".format(
                    self.vrp_name, LOCAL_RP_NAME_PATH
                )
            )
            make_file_dir(LOCAL_RP_NAME_PATH)
            with open(LOCAL_RP_NAME_PATH, "w") as f:
                f.write(self.vrp_name)

    def teardown_method(self):
        """Method to delete creates bps and apps during tests"""

        for bp_name in self.created_bp_list:
            LOG.info("Deleting Blueprint {}".format(bp_name))
            runner = CliRunner()
            result = runner.invoke(cli, ["delete", "bp", bp_name])
            assert result.exit_code == 0

        for app_name in self.created_app_list:
            LOG.info("Deleting app {}".format(app_name))
            self._delete_app(app_name)

        self.created_app_list = []
        self.created_bp_list = []

    def _delete_app(self, app_name):

        runner = CliRunner()
        self.app_helper._wait_for_non_busy_state(app_name)
        LOG.info("Deleting App {} ".format(app_name))
        result = runner.invoke(cli, ["delete", "app", app_name])
        assert result.exit_code == 0
        LOG.info("App {} deleted successfully".format(app_name))

    def _create_bp(self, name, bp_path):

        runner = CliRunner()

        LOG.info("Creating Bp {}".format(name))
        result = runner.invoke(
            cli,
            [
                "create",
                "bp",
                "--file={}".format(bp_path),
                "--name={}".format(name),
                "--description='Test DSL Blueprint to delete'",
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
            pytest.fail("Blueprint creation failed")

        else:
            LOG.debug("Response: {}".format(result.output))

    def _write_snapshot_launch_params(self, bp_name):
        """
        Dynamically generates a launch_params Python file that pre-selects the
        protection policy and local rule for the blueprint's snapshot config.

        This answers the "Select Policy" and "Select Local Rule" prompts on the
        BP launch page without requiring interactive input, by writing a file
        consumed via --launch_params.

        The value dict written has the shape expected by bps.py:
            snapshot_config["value"] = {
                "attrs_list": [{
                    "app_protection_policy_reference": "<policy-uuid>",
                    "app_protection_rule_reference":   "<rule-uuid>",
                }]
            }
        """
        client = get_api_client()

        # ── 1. Get blueprint UUID and spec ────────────────────────────────────
        res, err = client.blueprint.list(
            params={"filter": "name=={}".format(bp_name), "length": 1}
        )
        if err:
            pytest.fail(
                "Failed to look up blueprint '{}': [{}] - {}".format(
                    bp_name, err["code"], err["error"]
                )
            )
        entities = res.json().get("entities", [])
        if not entities:
            pytest.fail("Blueprint '{}' not found".format(bp_name))
        bp_uuid = entities[0]["metadata"]["uuid"]

        res, err = client.blueprint.read(bp_uuid)
        if err:
            pytest.fail(
                "Failed to read blueprint '{}': [{}] - {}".format(
                    bp_name, err["code"], err["error"]
                )
            )
        bp_data = res.json()
        app_profile = bp_data["spec"]["resources"]["app_profile_list"][0]
        app_profile_uuid = app_profile["uuid"]

        snapshot_config = app_profile["snapshot_config_list"][0]
        snapshot_config_name = snapshot_config["name"]
        snapshot_config_uuid = snapshot_config["uuid"]

        # ── 2. Resolve environment UUID from ENV_NAME ─────────────────────────
        res, err = client.environment.list(
            params={"filter": "name=={}".format(ENV_NAME), "length": 1}
        )
        if err:
            pytest.fail(
                "Failed to list environments: [{}] - {}".format(
                    err["code"], err["error"]
                )
            )
        env_entities = res.json().get("entities", [])
        if not env_entities:
            pytest.fail("Environment '{}' not found".format(ENV_NAME))
        env_uuid = env_entities[0]["metadata"]["uuid"]
        # ── 3. Fetch protection policies for this snapshot config + env ────────
        res, err = client.blueprint.protection_policies(
            bp_uuid, app_profile_uuid, snapshot_config_uuid, env_uuid
        )
        if err:
            pytest.fail(
                "Failed to fetch protection policies: [{}] - {}".format(
                    err["code"], err["error"]
                )
            )
        protection_policies = [p["status"] for p in res.json().get("entities", [])]
        # ── 4. Find policy matching SNAPSHOT_POLICY_NAME ──────────────────────
        selected_policy = next(
            (p for p in protection_policies if p["name"] == SNAPSHOT_POLICY_NAME),
            None,
        )
        if not selected_policy:
            pytest.fail(
                "Protection policy '{}' not found. Available: {}".format(
                    SNAPSHOT_POLICY_NAME,
                    [p["name"] for p in protection_policies],
                )
            )
        policy_uuid = selected_policy["uuid"]

        # ── 5. Find local rule matching LOCAL_RULE_NAME ───────────────────────
        selected_rule = next(
            (
                r
                for r in selected_policy["resources"]["app_protection_rule_list"]
                if r["name"] == LOCAL_RULE_NAME
            ),
            None,
        )
        if not selected_rule:
            rule_names = [
                r["name"]
                for r in selected_policy["resources"]["app_protection_rule_list"]
            ]
            pytest.fail(
                "Local rule '{}' not found in policy '{}'. Available rules: {}".format(
                    LOCAL_RULE_NAME, SNAPSHOT_POLICY_NAME, rule_names
                )
            )
        rule_uuid = selected_rule["uuid"]

        # ── 6. Write the launch_params Python file ────────────────────────────
        content = (
            "# Auto-generated by TestVmRecoveryPointBp._write_snapshot_launch_params\n"
            "# Policy : {policy_name} ({policy_uuid})\n"
            "# Rule   : {rule_name}   ({rule_uuid})\n"
            "\n"
            "snapshot_config_list = [\n"
            "    {{\n"
            '        "name": "{config_name}",\n'
            '        "value": {{\n'
            '            "attrs_list": [\n'
            "                {{\n"
            '                    "app_protection_policy_reference": "{policy_uuid}",\n'
            '                    "app_protection_rule_reference": "{rule_uuid}",\n'
            "                }}\n"
            "            ]\n"
            "        }},\n"
            "    }}\n"
            "]\n"
        ).format(
            config_name=snapshot_config_name,
            policy_name=SNAPSHOT_POLICY_NAME,
            policy_uuid=policy_uuid,
            rule_name=LOCAL_RULE_NAME,
            rule_uuid=rule_uuid,
        )

        make_file_dir(SNAPSHOT_LAUNCH_PARAMS_PATH)
        with open(SNAPSHOT_LAUNCH_PARAMS_PATH, "w") as f:
            f.write(content)

        LOG.info(
            "Snapshot launch params written to '{}' "
            "(policy='{}', rule='{}')".format(
                SNAPSHOT_LAUNCH_PARAMS_PATH, SNAPSHOT_POLICY_NAME, LOCAL_RULE_NAME
            )
        )
        return SNAPSHOT_LAUNCH_PARAMS_PATH

    def _launch_bp(self, bp_name, app_name):
        """
        Launches a blueprint.

        Uses --launch_params (instead of -i) so that the snapshot configuration
        fields "Select Policy" and "Select Local Rule" are pre-filled without
        interactive prompts.  Using -i with snapshot configs is blocked by the
        DSL (CALM-39565) when no policy is pre-set in the blueprint.
        """
        launch_params_path = self._write_snapshot_launch_params(bp_name)

        runner = CliRunner()
        LOG.info(
            "Launching bp {} to create app {} with environment {} "
            "and snapshot launch params {}".format(
                bp_name, app_name, ENV_NAME, launch_params_path
            )
        )
        result = runner.invoke(
            cli,
            [
                "launch",
                "bp",
                bp_name,
                "--app_name={}".format(app_name),
                "-e",
                ENV_NAME,
                "--launch_params={}".format(launch_params_path),
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
            pytest.fail("App creation failed")

        else:
            LOG.debug("Response: {}".format(result.output))

    def _get_app_uuid(self, app_name):

        runner = CliRunner()
        result = runner.invoke(cli, ["describe", "app", app_name, "--out=json"])
        app_data = json.loads(result.output)
        return app_data["metadata"]["uuid"]

    def _create_vm_recovery_point(self):

        # Create blueprint
        bp_name = "Blueprint{}".format(str(uuid.uuid4())[:10])
        self._create_bp(bp_name, NORMAL_DSL_BP_FILEPATH)
        self.created_bp_list.append(bp_name)

        # Create application
        app_name = "App{}".format(str(uuid.uuid4())[:10])
        self._launch_bp(bp_name, app_name)
        self.created_app_list.append(app_name)

        # Wait for app creation completion
        self.app_helper._wait_for_non_busy_state(app_name)
        LOG.info("Application {} created successfully".format(app_name))
        vm_recovery_point_name = "VRP-{}".format(str(uuid.uuid4())[:10])
        LOG.info("Creating snapshot {} via run_action".format(vm_recovery_point_name))
        vm_recovery_point_uuid = self._run_snapshot_action(
            app_name, vm_recovery_point_name, SNAPSHOT_ACTION_NAME
        )

        self.vrp_name = vm_recovery_point_name
        self.vrp_uuid = vm_recovery_point_uuid

        return {"name": vm_recovery_point_name, "uuid": vm_recovery_point_uuid}

    def _run_snapshot_action(self, app_name, vm_recovery_point_name, action_name):
        """
        Triggers a snapshot action on the given app using the Calm DSL run_action API
        and returns the resulting VM recovery point UUID.

        Uses client.application.run_action instead of the PC API (mh_vms/<uuid>/snapshot)
        to ensure compatibility with NCM 2.0.
        """
        client = get_api_client()

        runner = CliRunner()
        result = runner.invoke(cli, ["describe", "app", app_name, "--out=json"])
        app = json.loads(result.output)
        app_id = app["metadata"]["uuid"]
        app_spec = app["spec"]
        status = app["status"]

        # Locate the snapshot action by its name (or prefixed form "action_<name>")
        calm_action_name = "action_" + action_name.lower()
        action_payload = next(
            (
                action
                for action in app_spec["resources"]["action_list"]
                if action["name"] == calm_action_name or action["name"] == action_name
            ),
            None,
        )
        if not action_payload:
            pytest.fail(
                "Snapshot action '{}' not found in app '{}'".format(
                    action_name, app_name
                )
            )

        action_id = action_payload["uuid"]

        # Build the snapshot_name argument for each CALL_CONFIG task in the action
        action_args = []
        config_list = status["resources"].get("snapshot_config_list", [])
        for task in action_payload["runbook"]["task_definition_list"]:
            if task["type"] == "CALL_CONFIG":
                config = next(
                    (
                        c
                        for c in config_list
                        if c["uuid"] == task["attrs"]["config_spec_reference"]["uuid"]
                    ),
                    None,
                )
                if config:
                    action_args.append(
                        {
                            "name": "snapshot_name",
                            "value": vm_recovery_point_name,
                            "task_uuid": task["uuid"],
                        }
                    )

        app.pop("status", None)
        app["spec"] = {
            "args": action_args,
            "target_kind": "Application",
            "target_uuid": app_id,
        }

        res, err = client.application.run_action(app_id, action_id, app)
        if err:
            pytest.fail(
                "Failed to trigger snapshot action: [{}] - {}".format(
                    err["code"], err["error"]
                )
            )

        runlog_uuid = res.json()["status"]["runlog_uuid"]
        LOG.info(
            "Snapshot action triggered on app '{}'. Runlog UUID: {}".format(
                app_name, runlog_uuid
            )
        )

        # Poll the runlog until the action reaches a terminal state
        poll_url = client.application.item_path.format(app_id) + "/app_runlogs/list"
        poll_payload = {"filter": "root_reference=={}".format(runlog_uuid)}
        max_wait = 10 * 60
        elapsed = 0
        poll_interval = 10

        while elapsed < max_wait:
            res, err = client.application.poll_action_run(poll_url, poll_payload)
            if err:
                pytest.fail(
                    "Failed to poll snapshot action runlog: [{}] - {}".format(
                        err["code"], err["error"]
                    )
                )
            entities = res.json().get("entities", [])
            if entities:
                sorted_entities = sorted(
                    entities, key=lambda x: int(x["metadata"]["creation_time"])
                )
                all_terminal = True
                for runlog in sorted_entities:
                    state = runlog["status"]["state"]
                    if state in RUNLOG.FAILURE_STATES:
                        pytest.fail(
                            "Snapshot action failed with state: {}".format(state)
                        )
                    elif state not in RUNLOG.TERMINAL_STATES:
                        all_terminal = False
                        break
                if all_terminal:
                    LOG.info("Snapshot action completed successfully")
                    break

            elapsed += poll_interval
            time.sleep(poll_interval)
        else:
            pytest.fail(
                "Snapshot action did not complete within {} seconds".format(max_wait)
            )

        # Fetch the newly created VM recovery point UUID by name.
        #
        # NOTE: The backend requires an account_uuid filter, but does not reliably
        # support server-side filtering by name for vm_recovery_points. So we
        # page through the account-scoped list and match by entity status.name.
        rp_max_wait = 3 * 60
        rp_elapsed = 0
        rp_poll_interval = 10
        vm_recovery_point_uuid = ""

        while rp_elapsed < rp_max_wait and not vm_recovery_point_uuid:
            page_len = 50
            offset = 0
            total_matches = None

            while total_matches is None or offset < total_matches:
                res, err = client.vm_recovery_point.list(
                    params={
                        "filter": "account_uuid=={}".format(ACC_UUID),
                        "length": page_len,
                        "offset": offset,
                    }
                )
                if err:
                    pytest.fail(
                        "Failed to list VM recovery points: [{}] - {}".format(
                            err["code"], err["error"]
                        )
                    )

                payload = res.json()
                total_matches = payload.get("metadata", {}).get("total_matches", 0)
                entities = payload.get("entities", [])
                for entity in entities:
                    if entity.get("status", {}).get("name") == vm_recovery_point_name:
                        vm_recovery_point_uuid = entity["metadata"]["uuid"]
                        break

                if vm_recovery_point_uuid:
                    break
                offset += page_len

            if not vm_recovery_point_uuid:
                time.sleep(rp_poll_interval)
                rp_elapsed += rp_poll_interval

        if not vm_recovery_point_uuid:
            pytest.fail(
                "VM recovery point '{}' not found after snapshot action".format(
                    vm_recovery_point_name
                )
            )

        LOG.info(
            "VM recovery point '{}' created with UUID: {}".format(
                vm_recovery_point_name, vm_recovery_point_uuid
            )
        )
        return vm_recovery_point_uuid

    def test_bp_compile_having_rp(self):
        """
        Steps:
            1. Create vm-recovery-point
            2. Compile blueprint having vm-recovery-point
        """

        runner = CliRunner()
        LOG.info("Compiling Bp {}".format(VRC_DSL_BP_FILEPATH))
        result = runner.invoke(
            cli,
            [
                "compile",
                "bp",
                "--file={}".format(VRC_DSL_BP_FILEPATH),
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
            pytest.fail("App creation failed")

        bp_json = json.loads(result.output)
        assert (
            bp_json["spec"]["resources"]["substrate_definition_list"][0][
                "recovery_point_reference"
            ]["uuid"]
            == self.vrp_uuid
        )
        assert (
            bp_json["spec"]["resources"]["substrate_definition_list"][0][
                "recovery_point_reference"
            ]["name"]
            == self.vrp_name
        )

    def test_bp_launch_having_vm_rp(self):
        """
        Steps:
            1. Create Blueprint
            2. Create App
            3. Create snapshot
            4. Create bp using that vm-recovery point
            5. Launch blueprint
        """

        # Create blueprint
        bp_name = "Blueprint{}".format(str(uuid.uuid4())[:10])
        self._create_bp(bp_name, VRC_DSL_BP_FILEPATH)
        self.created_bp_list.append(bp_name)

        # Create application
        app_name = "App{}".format(str(uuid.uuid4())[:10])
        self._launch_bp(bp_name, app_name)
        self.created_app_list.append(app_name)

        # Wait for app creation completion
        self.app_helper._wait_for_non_busy_state(app_name)
        LOG.info("Application {} created successfully".format(app_name))

    @pytest.mark.skipif(
        LV(CALM_VERSION) < LV(CONFIG_TYPE.RESTORE.RESTORE_TYPE_MIN_VERSION),
        reason="restore_type REVERT not supported (requires Calm >= {})".format(
            CONFIG_TYPE.RESTORE.RESTORE_TYPE_MIN_VERSION
        ),
    )
    def test_inplace_restore_preserves_vm_uuid(self):
        """
        Verifies that in-place restore (revert) preserves the VM UUID.

        Steps:
            1. Create blueprint
            2. Launch app
            3. Record the VM UUID
            4. Take a snapshot
            5. Run in-place restore
            6. Verify VM UUID is unchanged
        """

        bp_name = "InPlaceRP-{}".format(str(uuid.uuid4())[:10])
        self._create_bp(bp_name, NORMAL_DSL_BP_FILEPATH)
        self.created_bp_list.append(bp_name)

        app_name = "InPlaceApp-{}".format(str(uuid.uuid4())[:10])
        self._launch_bp(bp_name, app_name)
        self.created_app_list.append(app_name)

        self.app_helper._wait_for_non_busy_state(app_name)
        LOG.info("Application {} created successfully".format(app_name))

        vm_uuid_before = self.app_helper.get_vm_uuid_from_app(app_name)
        assert vm_uuid_before, "Could not extract VM UUID from app '{}'".format(
            app_name
        )
        LOG.info("VM UUID before snapshot: {}".format(vm_uuid_before))

        snapshot_name = "InPlaceSnap-{}".format(str(uuid.uuid4())[:10])
        self._run_snapshot_action(app_name, snapshot_name, "Snapshot_s1")
        self.app_helper._wait_for_non_busy_state(app_name)
        LOG.info("Snapshot {} created".format(snapshot_name))

        self.app_helper.run_restore_action(app_name, "Restore_r1")
        self.app_helper._wait_for_non_busy_state(app_name)
        LOG.info("In-place restore completed")

        vm_uuid_after = self.app_helper.get_vm_uuid_from_app(app_name)
        assert (
            vm_uuid_after
        ), "Could not extract VM UUID from app '{}' after restore".format(app_name)
        LOG.info("VM UUID after restore: {}".format(vm_uuid_after))

        assert (
            vm_uuid_before == vm_uuid_after
        ), "VM UUID changed after in-place restore: before={}, after={}".format(
            vm_uuid_before, vm_uuid_after
        )
