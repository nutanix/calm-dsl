# escript test
import uuid
import pytest
import os
import json


from calm.dsl.log import get_logging_handle
from calm.dsl.cli import runbooks
from calm.dsl.api import get_api_client
from calm.dsl.cli.constants import RUNLOG
from calm.dsl.runbooks import read_local_file
from tests.utils import poll_runlog_status


LOG = get_logging_handle(__name__)

RUNBOOK_DSL_FILE_NAME_PREFIX = "dsl_escript_parallel_runbook"

ESCRIPT_BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts/")

DEFAULT_ESCRIPT_TIMEOUT = 60

# create DSL file on the fly
runbook_dsl_input = [
    "from calm.dsl.runbooks import runbook, runbook_json, parallel, branch",
    "from calm.dsl.runbooks import RunbookTask as Task",
    "",
    "@runbook",
    "def SampleRunbook():",
    "    with parallel() as p:",
    "#replace_task",
    "",
]


def dsl_file_udpate(
    runbook_dsl_file, escript, escript_version="static", parallel_count=10
):
    escript_name = escript.split(".")[0]
    with open(runbook_dsl_file, "w") as fd:
        for line in runbook_dsl_input:
            if "#replace_task" in line:
                for i in range(parallel_count):
                    task_ln = '        with branch(p):\n            Task.Exec.escript(name="{}_{}",filename="{}")'.format(
                        escript_name, i + 1, os.path.join(ESCRIPT_BASE_PATH, escript)
                    )
                    fd.write(task_ln)
                    fd.write("\n")
            else:
                fd.write(line)
                fd.write("\n")


def get_escript_version_status(escript):
    with open(os.path.join(ESCRIPT_BASE_PATH, escript)) as fd:
        first_line = fd.readline()
        if "success" in first_line.lower():
            script_pass = RUNLOG.STATUS.SUCCESS
        elif "failure" in first_line.lower():
            script_pass = RUNLOG.STATUS.FAILURE
        else:
            script_pass = RUNLOG.STATUS.SUCCESS
        if "python3" in first_line.lower() or "py3" in first_line.lower():
            # FIXME: chnage once python3 support lands
            script_version = "static"
        elif "python2" in first_line.lower() or "py2" in first_line.lower():
            script_version = "static"
        else:
            # default to python2 for now, pls fix python scripts
            script_version = "static"
        try:
            script_timeout = int(first_line.split(";")[2])
        except IndexError:
            script_timeout = DEFAULT_ESCRIPT_TIMEOUT
    return (script_version, script_pass, script_timeout)


@pytest.mark.escript
class TestEscript:
    @pytest.mark.parametrize(
        "escript, parallel_count",
        [
            pytest.param("parallel_escript_py3.py", 60),
            pytest.param("parallel_escript_py2.py", 60),
        ],
    )
    def test_run_parallel_escript_via_runbook(self, escript, parallel_count):
        """
        Test run escript with parallel task
        """
        errors_map = {}
        client = get_api_client()
        folder_path = os.path.dirname(os.path.abspath(__file__))
        runbook_dsl_file = os.path.join(
            folder_path,
            "dsl_file/",
            "{}_{}".format(RUNBOOK_DSL_FILE_NAME_PREFIX, escript),
        )
        # Let's build a DSL file for python scripts in scripts folder
        (
            script_version,
            expected_script_status,
            script_timeout,
        ) = get_escript_version_status(escript)
        dsl_file_udpate(
            runbook_dsl_file,
            escript,
            escript_version=script_version,
            parallel_count=parallel_count,
        )
        LOG.info("runbook dsl file used {}".format(runbook_dsl_file))
        runbook_name = "escript_parallel_runbook_{}".format(str(uuid.uuid4())[-12:])
        # get script output
        try:
            file_path = "{}.out".format(os.path.join(ESCRIPT_BASE_PATH, escript))
            with open(file_path) as fd:
                exp_script_output = fd.read()
        except IOError:
            # skip output check if no out file in environment
            exp_script_output = None
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
                client,
                runlog_uuid,
                RUNLOG.TERMINAL_STATES,
                maxWait=script_timeout + parallel_count,
            )
            LOG.debug(">> Runbook Run state: {}\n{}".format(state, reasons))
            assert state == expected_script_status, reasons

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
                if escript.split(".")[0] not in script_name:
                    continue
                else:
                    errors_map[script_name] = []
                LOG.info(
                    "Checking status and output for escript: {}".format(script_name)
                )
                res, err = client.runbook.runlog_output(
                    runlog_uuid, entity["metadata"]["uuid"]
                )
                response = res.json()
                actual_output = response["status"]["output_list"][0]["output"]
                if expected_script_status != script_status:
                    err_msg = """Mismatch in status for script: {}
                    Expected status: {} 
                    Actual status: {}
                    """.format(
                        script_name, expected_script_status, script_status
                    )
                    errors_map[script_name].append(err_msg)
                if exp_script_output and actual_output != exp_script_output:
                    err_msg = """Mismatch in output for script: {}
                    Expected output: {} 
                    Actual output: {}
                    """.format(
                        script_name, exp_script_output, actual_output
                    )
                    errors_map[script_name].append(err_msg)
            if any(errors_map.values()):
                LOG.info("Got below exception during test")
                for escript, error in errors_map.items():
                    if error:
                        LOG.error(
                            "\nErrors of escript: {} can be found below".format(escript)
                        )
                        for err in error:
                            LOG.error("{}".format(err))
                assert False, errors_map
            else:
                client.runbook.delete(runbook_uuid)
        except Exception as error:
            LOG.info("Got exception during test: {}".format(error))
            assert False, error
