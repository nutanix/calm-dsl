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
from tests.utils import get_escript_language_from_version

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))


LOG = get_logging_handle(__name__)

RUNBOOK_DSL_FILE_NAME_PREFIX = "dsl_escript_runbook"


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


def get_actual_script_status(client, runlog_uuid, script_name):
    """parse given runbook execution status and provide
    actual status map
    """
    res, err = client.runbook.list_runlogs(runlog_uuid)
    if err:
        return (RUNLOG.STATUS.FAILURE, err)
    response = res.json()
    entities = sorted(
        response["entities"], key=lambda x: int(x["metadata"]["creation_time"])
    )
    exp_entity = None
    for entity in entities:
        if script_name in entity.get("status", {}).get("task_reference", {}).get(
            "name", ""
        ):
            exp_entity = entity
            break
    if not exp_entity:
        return (RUNLOG.STATUS.FAILURE, err)
    script_status = exp_entity.get("status", {}).get("state", RUNLOG.STATUS.FAILURE)
    LOG.info("Checking status and output for escript: {}".format(script_name))
    res, err = client.runbook.runlog_output(runlog_uuid, exp_entity["metadata"]["uuid"])
    response = res.json()
    script_output = response["status"]["output_list"][0]["output"]
    return (script_status, script_output)


@pytest.mark.escript
class TestEscript:
    def setup_class(self):
        """setup class method"""
        folder_path = os.path.dirname(os.path.abspath(__file__))
        escript_folder = os.path.join(folder_path, "scripts/")
        escript_files_list = sorted(os.listdir(escript_folder))
        # {'dsl_file_path': (script_name, script_content, script_version, script_output, script_pass)}
        # Eg:- {'/path/to/dsl/file.py':('escript1', '#python2;success\nprint "hi"', 'py3', 'hi\n', True)}
        self.script_dsl_file_map = {}
        for script in escript_files_list:
            if not script.endswith(".py"):
                continue
            script_name = script.split(".")[0]
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
                    script_version = "static_py3"
                elif "python2" in first_line.lower() or "py2" in first_line.lower():
                    script_version = "static"
                else:
                    # default to python2 for now, pls fix python scripts
                    script_version = "static"
                    script_content = first_line + "\n" + script_content
            script_language = get_escript_language_from_version(script_version)
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
            # Let's build a DSL file(s) for python scripts in scripts folder
            filename = (
                RUNBOOK_DSL_FILE_NAME_PREFIX + str(uuid.uuid4()).split("-")[0] + ".py"
            )
            runbook_dsl_file = folder_path + "/dsl_file/" + filename
            self.script_dsl_file_map[runbook_dsl_file] = (
                script_name,  # python(escript) script content
                script_content,  # python(escript) script content
                script_version,  # python(escript) script version
                script_output,  # python(escript) script output
                script_pass,  # python(escript) script expected status
                script_language,  # python(escript) script language
            )
            with open(runbook_dsl_file, "w") as fd:
                for line in runbook_dsl_input:
                    if "#scripts" in line:
                        fd.write("script_{}_{}='''".format(script_name, script_version))
                        fd.write("\n")
                        fd.write(script_content)
                        fd.write("\n")
                        fd.write("'''")
                        fd.write("\n")
                    elif "#replace_task" in line:
                        task_ln = '    Task.Exec.escript{}(name="{}", script=script_{}_{})'.format(
                            script_language, script_name, script_name, script_version
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
        client = get_api_client()
        errors_map = {}
        for runbook_dsl_file, script_details in self.script_dsl_file_map.items():
            LOG.info("runbook dsl file used {}".format(runbook_dsl_file))
            runbook_name = "runbook_{}_{}".format(
                script_details[0], str(uuid.uuid4())[-12:]
            )
            errors_map[runbook_name] = []
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
                    client, runlog_uuid, RUNLOG.TERMINAL_STATES, maxWait=30
                )
                LOG.debug(">> Runbook Run state: {}\n{}".format(state, reasons))
                # assert for overall runbook status
                if script_details[4]:
                    expected_overall_status = [RUNLOG.STATUS.SUCCESS]
                else:
                    expected_overall_status = [
                        RUNLOG.STATUS.FAILURE,
                        RUNLOG.STATUS.ERROR,
                    ]

                # check for overall status
                if state not in expected_overall_status:
                    err_msg = """Runbook is in unexpected state
                    Expected: {}
                    Actual: {}
                    """.format(
                        expected_overall_status, state
                    )
                    if reasons:
                        err_msg += "due to  {}".format(reasons)
                    errors_map[runbook_name].append(err_msg)
                actual_script_status, actual_script_output = get_actual_script_status(
                    client, runlog_uuid, script_details[0]
                )
                # check for script output
                if script_details[3] != actual_script_output:
                    err_msg = """Mismatch in Output:
                    Expected output: {} 
                    Actual output: {}
                    """.format(
                        script_details[3], actual_script_output
                    )
                    errors_map[runbook_name].append(err_msg)
                # check for script status
                if actual_script_status not in expected_overall_status:
                    err_msg = """Mismatch in Status:
                    Expected status: {} 
                    Actual status: {}
                    """.format(
                        expected_overall_status, actual_script_status
                    )
                    errors_map[runbook_name].append(err_msg)
                # delete runbook when no failures
                if not errors_map[runbook_name]:
                    runbooks.delete_runbook([runbook_name])
                else:
                    LOG.error("runbook: {} encountered error".format(runbook_name))
            except Exception as error:
                LOG.info(
                    "Got below exception during test for runbook: {} created using dsl file: {}\n Exception: {}".format(
                        runbook_name, runbook_dsl_file, error
                    )
                )
                errors_map[runbook_name].append("Got exception: {}".format(error))
        if any(errors_map.values()):
            LOG.info("Got below exception during test")
            for runbook, error in errors_map.items():
                if error:
                    LOG.error(
                        "\nErrors of runbook: {} can be found below".format(runbook)
                    )
                    for err in error:
                        LOG.error("{}".format(err))
            assert False, errors_map
