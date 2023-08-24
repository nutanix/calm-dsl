# escript test
import uuid
import pytest
import os
import time

# from distutils.version import LooseVersion as LV
# from calm.dsl.store import Version

from calm.dsl.log import get_logging_handle
from calm.dsl.cli import runbooks
from calm.dsl.api import get_api_client
from calm.dsl.cli.constants import RUNLOG
import json
from calm.dsl.runbooks import read_local_file

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))


LOG = get_logging_handle(__name__)

RUNBOOK_DSL_FILE_NAME = "dsl_escript_runbook.py"


def poll_runlog_status(
    client, runlog_uuid, expected_states, poll_interval=10, maxWait=300
):
    """
    This routine polls for 5mins till the runlog gets into the expected state
    Args:
        client (obj): client object
        runlog_uuid (str): runlog id
        expected_states (list): list of expected states
    Returns:
        (str, list): returns final state of the runlog and reasons list
    """
    count = 0
    while count < maxWait:
        res, err = client.runbook.poll_action_run(runlog_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        response = res.json()
        LOG.debug(response)
        state = response["status"]["state"]
        reasons = response["status"]["reason_list"]
        if state in expected_states:
            break
        count += poll_interval
        time.sleep(poll_interval)

    return state, reasons or []


# create DSL file on the fly
runbook_dsl_input = [
    "from calm.dsl.runbooks import runbook, runbook_json",
    "from calm.dsl.runbooks import RunbookTask as Task",
    "#scripts",
    "@runbook",
    "def SampleRunbook():",
    "#replace_task",
    "def main():",
    "    print(runbook_json(SampleRunbook))",
    'if __name__ == "__main__":',
    "    main()",
]

# calm_version
# CALM_VERSION = Version.get_version("Calm")
# LIST_FILTER_LEN = 200

# @pytest.mark.skipif(
#    LV(CALM_VERSION) < LV("3.9.0"), reason="goGadarz FEAT is for v3.9.0"
# )


@pytest.mark.escript
class TestEscript:
    def setup_class(self):
        """setup class method"""
        folder_path = os.path.dirname(os.path.abspath(__file__))
        escript_folder = os.path.join(folder_path, "scripts/")
        escript_files_list = sorted(os.listdir(escript_folder))
        # {'scipt_file_name': (script_content, script_version, script_output, script_pass)} Eg:- {'escript1':('#python2;success\nprint "hi"', 'py3', 'hi\n', True)}
        self.script_map = {}
        for script in escript_files_list:
            if not script.endswith(".py"):
                continue
            file_path = os.path.join(escript_folder, script)
            with open(file_path) as fd:
                first_line = fd.readline()
                script_content = fd.read()
                if "success" in first_line.lower():
                    script_pass = True
                elif "failure" in first_line.lower():
                    script_pass = False
                else:
                    script_pass = True
                if "python3" in first_line.lower() or "py3" in first_line.lower():
                    script_version = "static"
                elif "python2" in first_line.lower() or "py2" in first_line.lower():
                    script_version = "static"
                else:
                    # default to python2 for now, pls fix python scripts
                    script_version = "static"
                    script_content = first_line + "\n" + script_content
            try:
                file_path = "{}.out".format(file_path)
                with open(file_path) as fd:
                    script_output = fd.read()
            except IOError:
                # skip output check if no out file in environment
                script_output = None
            provider = script.split(".")[0].split("_")
            if len(provider) > 1:
                provider = provider[1]
            else:
                provider = None
            provider_config = DSL_CONFIG["provider"].get(provider, None)
            if provider_config:
                for replace_key, replace_item in provider_config.items():
                    script_content = script_content.replace(replace_key, replace_item)
            self.script_map[script.split(".")[0]] = (
                script_content,
                script_version,
                script_output,
                script_pass,
            )
        # Let's build a DSL file for python scripts in scripts folder
        runbook_dsl_file = folder_path + "/dsl_file/" + RUNBOOK_DSL_FILE_NAME
        with open(runbook_dsl_file, "w") as fd:
            for line in runbook_dsl_input:
                if "#scripts" in line:
                    for val, script in self.script_map.items():
                        fd.write("script_{}_{}='''".format(val, script[1]))
                        fd.write("\n")
                        fd.write(script[0])
                        fd.write("\n")
                        fd.write("'''")
                        fd.write("\n")
                elif "#replace_task" in line:
                    for val, script in self.script_map.items():
                        task_ln = '    Task.Exec.escript(name="{}", script=script_{}_{})'.format(
                            val, val, script[1]
                        )
                        fd.write(task_ln)
                        fd.write("\n")
                else:
                    fd.write(line)
                    fd.write("\n")

    def test_run_escript_via_runbook(self):
        """
        Test run escript via runbook
        Creates a sample runbook with escript task created from list of scripts from scripts folder
        Asserts the status and output of escript based on the response set by script comment in first line
        and script.out file for expected output
        sample escript
        > cat escript1.py
        #python2;success
        print "hi"
        >cat escript.py.out
        hi

        >cat escript2.py
        #python2;failure
        pi
        >cat escript.py.out
        Error at line 3> name 'pi' is not defined

        """
        print(self.script_map)
        client = get_api_client()
        folder_path = os.path.dirname(os.path.abspath(__file__))
        runbook_dsl_file = folder_path + "/dsl_file/" + RUNBOOK_DSL_FILE_NAME
        LOG.info("runbook dsl file used {}".format(RUNBOOK_DSL_FILE_NAME))
        runbook_name = "escript_runbook_{}".format(str(uuid.uuid4())[-12:])
        # Create runbook
        res = runbooks.create_runbook_command(
            runbook_dsl_file, runbook_name, description="", force=True
        )
        try:
            # Get runbook uuid
            runbook_uuid = runbooks.get_runbook(client, runbook_name)["metadata"][
                "uuid"
            ]
            # Execute runbook
            res, err = client.runbook.run(runbook_uuid, {})
            if err:
                LOG.info("run: response: {}\n err: {}".format(res, err))
                assert False, "Runbook execution failed"
            response = res.json()
            LOG.debug(">> Runbook execute response: {}".format(response))
            runlog_uuid = response["status"]["runlog_uuid"]

            # polling till runbook run gets to terminal state
            state, reasons = poll_runlog_status(
                client, runlog_uuid, RUNLOG.TERMINAL_STATES, maxWait=60
            )
            LOG.debug(">> Runbook Run state: {}\n{}".format(state, reasons))
            # assert for overall runbook status
            if all([val[3] for key, val in self.script_map.items()]):
                expected_overall_status = RUNLOG.STATUS.SUCCESS
            else:
                expected_overall_status = RUNLOG.STATUS.FAILURE
            assert state == expected_overall_status, reasons

            # assert for overall task status ans output
            res, err = client.runbook.list_runlogs(runlog_uuid)
            response = res.json()
            entities = sorted(
                response["entities"], key=lambda x: int(x["metadata"]["creation_time"])
            )
            for entity in entities:
                script_name = (
                    entity.get("status", {}).get("task_reference", {}).get("name", "")
                )
                script_status = entity.get("status", {}).get(
                    "state", RUNLOG.STATUS.FAILURE
                )
                if script_name not in self.script_map.keys():
                    continue
                LOG.info(
                    "Checking status and output for escript: {}".format(script_name)
                )
                res, err = client.runbook.runlog_output(
                    runlog_uuid, entity["metadata"]["uuid"]
                )
                response = res.json()
                task_output = response["status"]["output_list"][0]["output"]
                assert (
                    self.script_map[script_name][2] == task_output
                ), "Script: {}\nExpected output: {}\nActual output:{}".format(
                    script_name, self.script_map[script_name][2], task_output
                )
                expected_status = (
                    RUNLOG.STATUS.SUCCESS
                    if self.script_map[script_name][3]
                    else RUNLOG.STATUS.FAILURE
                )
                assert (
                    expected_status == script_status
                ), "Script: {}\nExpected status:{}\nActual status: {}".format(
                    script_name, expected_status, script_status
                )
                if expected_status != RUNLOG.STATUS.SUCCESS:
                    # once task failed, next task won't be executed, so skip
                    break
        except Exception as error:
            LOG.info("Got exception during test: {}".format(error))
            assert False, error
        finally:
            runbooks.delete_runbook([runbook_name])
