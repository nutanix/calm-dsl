import os
import pytest
import re
import time
import json
import sys
import uuid
import traceback
import subprocess
import filecmp
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.cli.main import get_api_client
from calm.dsl.log import get_logging_handle
from calm.dsl.builtins import read_local_file
from tests.utils import Application as ApplicationHelper
from calm.dsl.cli.constants import APPLICATION

LOG = get_logging_handle(__name__)
FOLDER_PATH = os.path.dirname(__file__)

# Things to test
# Marketplace multi VM migrate.
# Unicode.
# Audit logs
# Invalid scenarios.
# API validations.
# Add new task shell/powershell/escript
# # Proifle level var secret.

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
# projects
PROJECT = DSL_CONFIG["PROJECTS"]["PROJECT1"]
PROJECT_NAME = PROJECT["NAME"]


@pytest.mark.nightly_380
@pytest.mark.skip
class TestMultiVmMigrate:
    app_helper = ApplicationHelper()

    @pytest.mark.parametrize(
        "test_file",
        [
            {
                "DSL_BP_FILEPATH": "specs/test_bp_python2_tasks_at_all_levels.py",
                "DSL_LAUNCH_PARAMS": "specs/variable_list_params.py",
                "action_to_run": ["python action"],
            },
            {
                "DSL_BP_FILEPATH": "specs/unicode_name_tasks_blueprint.py",
                "DSL_LAUNCH_PARAMS": "specs/variable_list_params.py",
                "action_to_run": ["片仮名 片仮名 python action"],
            },
        ],
    )
    def test_multivm_app_migrate(self, test_file):
        err_msg = []
        # Creating the blueprint with Python 2 tasks.
        client = get_api_client()
        runner = CliRunner()
        self.created_dsl_bp_name = "Test_Multi_VM_MIGRATE {}".format(int(time.time()))
        LOG.info(
            "Creating Bp {} using file {}".format(
                self.created_dsl_bp_name, test_file["DSL_BP_FILEPATH"]
            )
        )
        result = runner.invoke(
            cli,
            [
                "create",
                "bp",
                "--file={}".format(
                    os.path.join(FOLDER_PATH, test_file["DSL_BP_FILEPATH"])
                ),
                "--name={}".format(self.created_dsl_bp_name),
                "--description='Test Multi VM Migrate'",
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
            pytest.fail("Stage 1: BP creation from python file failed")
        LOG.info("Stage 1: BP creation Success")

        if (
            test_file["DSL_BP_FILEPATH"]
            == "specs/test_bp_python2_tasks_at_all_levels.py"
        ):

            self.marketplace_bp_name = "Test_Multi_VM_MIGRATE MPI {}".format(
                int(time.time())
            )
            self.mpi1_version = "1.0.0"

            # Publish Bp to marketplace manager as new marketplace blueprint
            LOG.info(
                "Publishing Bp {} as new marketplace blueprint {}".format(
                    self.created_dsl_bp_name, self.marketplace_bp_name
                )
            )
            command = [
                "publish",
                "bp",
                self.created_dsl_bp_name,
                "--version",
                self.mpi1_version,
                "--name",
                self.marketplace_bp_name,
                "--with_secrets",
            ]
            runner = CliRunner()

            result = runner.invoke(cli, command)
            if result.exit_code:
                cli_res_dict = {
                    "Output": result.output,
                    "Exception": str(result.exception),
                }
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
                pytest.fail(
                    "Stage2: Publishing of marketplace blueprint as new marketplace item failed"
                )
            LOG.info("Success")

            # Approve the blueprint
            LOG.info(
                "Approving marketplace blueprint {} with version {}".format(
                    self.marketplace_bp_name, self.mpi1_version
                )
            )
            command = [
                "approve",
                "marketplace",
                "bp",
                self.marketplace_bp_name,
                "--version",
                self.mpi1_version,
            ]

            result = runner.invoke(cli, command)
            if result.exit_code:
                cli_res_dict = {
                    "Output": result.output,
                    "Exception": str(result.exception),
                }
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
                pytest.fail("Stage2: Approving of marketplace blueprint failed")
            LOG.info("Success")

            # Publish blueprint to marketplace
            LOG.info(
                "Publishing marketplace blueprint {} with version {} to marketplace".format(
                    self.marketplace_bp_name, self.mpi1_version
                )
            )
            command = [
                "publish",
                "marketplace",
                "bp",
                self.marketplace_bp_name,
                "--version",
                self.mpi1_version,
                "--project",
                PROJECT_NAME,
            ]

            result = runner.invoke(cli, command)
            if result.exit_code:
                cli_res_dict = {
                    "Output": result.output,
                    "Exception": str(result.exception),
                }
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
                pytest.fail(
                    "Stage2: Publishing of marketplace blueprint to marketplace failed"
                )
            LOG.info("Success")

            # Launching the bp in PUBLISHED state(Marketplace Item) with launch_params
            self.created_app_name = "Test_MPI_APP_LP_{}".format(str(uuid.uuid4())[-10:])
            LOG.info(
                "Launching Marketplace Item {} with version {} with launch_params".format(
                    self.marketplace_bp_name, self.mpi1_version
                )
            )
            command = [
                "launch",
                "marketplace",
                "item",
                self.marketplace_bp_name,
                "--version",
                self.mpi1_version,
                "--project",
                PROJECT_NAME,
                "--app_name",
                self.created_app_name,
                "--profile_name",
                "Default",
                "--launch_params={}".format(
                    os.path.join(FOLDER_PATH, test_file["DSL_LAUNCH_PARAMS"])
                ),
            ]
            runner = CliRunner()

            result = runner.invoke(cli, command)
            if result.exit_code:
                cli_res_dict = {
                    "Output": result.output,
                    "Exception": str(result.exception),
                }
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
                pytest.fail(
                    "Stage2: Launching of marketplace blueprint in PUBLISHED state failed"
                )
            LOG.info("Success")

        else:
            # Application create
            self.created_app_name = "MultiVM__Migrate {}".format(
                self.created_dsl_bp_name
            )
            LOG.info("Launching Bp {}".format(self.created_dsl_bp_name))
            result = runner.invoke(
                cli,
                [
                    "launch",
                    "bp",
                    self.created_dsl_bp_name,
                    "--app_name={}".format(self.created_app_name),
                    "--launch_params={}".format(
                        os.path.join(FOLDER_PATH, test_file["DSL_LAUNCH_PARAMS"])
                    ),
                ],
            )
            if result.exit_code:
                cli_res_dict = {
                    "Output": result.output,
                    "Exception": str(result.exception),
                }
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
                pytest.fail("Stage 2: Blueprint launch failed")
        self.app_helper._wait_for_non_busy_state(self.created_app_name)
        result = runner.invoke(
            cli, ["describe", "app", self.created_app_name, "--out=json"]
        )
        app_data = json.loads(result.output)
        state = app_data["status"]["state"]
        if state not in APPLICATION.STATES.RUNNING:
            pytest.fail(
                f"Stage 2: Application is not in Running state, current state {state}"
            )
        LOG.info("Stage 2: App creation/launch Success")

        # MultiVM Application describe
        LOG.info("Describing the application {}".format(self.created_app_name))
        result = runner.invoke(
            cli, ["describe", "app-migratable-entities", self.created_app_name]
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
            err_msg.append(
                "Stage 3: App migratable entities describe command failed for app {}".format(
                    self.created_app_name
                )
            )

        # Application decompile
        LOG.info("Decompiling the migratable entities {}".format(self.created_app_name))
        result = runner.invoke(
            cli, ["decompile", "app-migratable-bp", "{}".format(self.created_app_name)]
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
            pytest.fail("Stage 3: App decompile failed")
        LOG.info("Stage 3: App decompile Success")

        # Validating the folder creation and files creation
        folder_name = "{}".format(
            str(
                app_data["status"]["resources"]["app_blueprint_config_reference"][
                    "name"
                ]
            )
            .replace(" ", "")
            .replace("-", "")
        )
        isExist = os.path.exists(folder_name)
        if not isExist:
            pytest.fail(
                "Stage 4: {} folder is not created after decompile app-migratable-bp ".format(
                    folder_name
                )
            )
        LOG.info("Stage 4: Folder with application name is present post decompile app")

        # Check all the required files created..
        required_files = ["blueprint.py", "scripts"]
        for file in required_files:
            file_path = os.path.join(folder_name, file)
            isExist = os.path.exists(file_path)

            if not isExist:
                pytest.fail(
                    "Required file {} is not created in folder {} after decompile app-migratable-bp".format(
                        file, folder_name
                    )
                )

            if file == "scripts":
                if os.listdir(file_path) == []:
                    pytest.fail(
                        "Scripts folder is empty after decompiling the app {}".format(
                            self.created_app_name
                        )
                    )

                try:
                    LOG.info("Futurizing the python 2 scripts to Python 3")

                    # Futurize works for simple python scripts
                    subprocess.run(
                        "futurize --stage1 -w --nobackups {}/*.py".format(file_path),
                        shell=True,
                    )
                except subprocess.CalledProcessError as e:
                    pytest.fail(f"Command {e.cmd} failed with error {e.returncode}")

                # After futurize, removing the additional import added
                for script_file in os.listdir(file_path):
                    script_file_path = os.path.join(file_path, script_file)
                    with open(script_file_path, "r") as script_file:
                        data = script_file.read()
                        data = data.replace(
                            "from __future__ import print_function", "#script"
                        )

                    with open(script_file_path, "w+") as script_file:
                        script_file.write(data)

            elif file == "blueprint.py":
                with open(file_path, "r") as blueprint_file:
                    data = blueprint_file.read()
                    data = data.replace("py2", "py3")
                with open(file_path, "w+") as blueprint_file:
                    blueprint_file.write(data)
                LOG.info("Change of function calls from py2 to py3 is done")

        LOG.info(
            "Stage 5: Decompile app-migratable-bp: Success. Required Files {} created".format(
                ", ".join(required_files)
            )
        )

        # Renaming the folder
        folder_original = "{}_original".format(folder_name)
        os.rename(folder_name, folder_original)

        # Application Update
        LOG.info("Updating the migratable entity {}".format(self.created_app_name))
        result = runner.invoke(
            cli,
            [
                "update",
                "app-migratable-bp",
                self.created_app_name,
                "--file={}".format(folder_original + "/blueprint.py"),
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
            pytest.fail("Stage 6: App update failed")
        self.app_helper._wait_for_non_busy_state(self.created_app_name)
        LOG.info("Stage 6: App update Success")

        # Validate the audit log update

        # Application re decompile
        LOG.info(
            "Re decompiling the migratable entities {}".format(self.created_app_name)
        )
        result = runner.invoke(
            cli, ["decompile", "app-migratable-bp", self.created_app_name]
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
            pytest.fail("Stage 7: App Re decompiling after update failed")
        LOG.info("Stage 7: App Re decompiling after update Success")

        # Final validation  in very concrete way.
        files_to_be_compared = ["scripts", "blueprint.py"]
        for file in files_to_be_compared:
            LOG.info(
                f"Stage 8: Comparing the content of {file} in folders {folder_original}, {folder_name}"
            )
            if file == "scripts":
                for script_file in os.listdir(os.path.join(folder_original, file)):
                    LOG.info(
                        f"Comparing the content of {script_file} in folders {file}"
                    )
                    new_file = os.path.join(folder_name, file, script_file)
                    original_file = os.path.join(folder_original, file, script_file)
                    val = filecmp.cmp(new_file, original_file)
                    if not val:
                        err_msg.append(
                            f"Stage 8: Contents in {original_file} and {new_file} are not identical, please check diff {val}"
                        )
                continue

            original_file_path = os.path.join(folder_original, file)
            new_file_path = os.path.join(folder_name, file)
            bp_val = filecmp.cmp(new_file_path, original_file_path)
            if not bp_val:
                err_msg.append(
                    f"Stage 8: Contents in blueprint.py is not identical, please check diff in {original_file_path} and {new_file_path}"
                )

        # Second Check: Run Actions which are updated.
        if test_file["action_to_run"]:
            LOG.info("Stage 9: checking app from app list api")
            params = {"filter": "name=={}".format(self.created_app_name)}
            res, err = client.application.list(params=params)
            if err:
                err_msg.append(
                    "Stage 9: app does not contain in app list, Error: [{}] - {}".format(
                        err["code"], err["error"]
                    )
                )

            response = res.json()
            entities = response.get("entities", None)
            app = None
            if not entities:
                pytest.fail(
                    "Stage 10: No entities found with the given app name {}".format(
                        self.created_app_name
                    )
                )
            app = entities[0]
            app_uuid = app["metadata"]["uuid"]
            res, err = client.application.read(app_uuid)
            if err:
                pytest.fail("Stage 11: application get call failed {}".format(err))

            app = res.json()

            # Run Custom action
            actions = test_file["action_to_run"]
            self.app_helper.execute_actions(actions, app)

        # Delete the app to cover post delete, package uninstall
        # let's wait for few seconds before delete
        result = runner.invoke(cli, ["delete", "app", self.created_app_name])
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
            pytest.fail("Stage 13: App delete failed")
        LOG.info("Stage 13: App delete Success")

        # poll for app delete action to be happened correctly
        LOG.info("Polling for delete operation on app {}".format(self.created_app_name))
        maxWait = 5 * 60
        count = 0
        poll_interval = 10
        while count < maxWait:
            res, err = client.application.read(app_uuid)
            if err:
                pytest.fail(err)

            res = res.json()
            state = res["status"]["state"]
            if state == APPLICATION.STATES.DELETED:
                LOG.info("App {} is deleted".format(self.created_app_name))
                break
            else:
                LOG.info("Application state: {}".format(state))

            count += poll_interval
            time.sleep(poll_interval)

        # Print all the failures results
        if err_msg:
            pytest.fail(
                "Error details for test {} {}".format(
                    test_file["DSL_BP_FILEPATH"], "\n".join(err_msg)
                )
            )
