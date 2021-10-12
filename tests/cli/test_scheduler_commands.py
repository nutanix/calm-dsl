import json
import time
import uuid
import pytest
import os as os_lib

from distutils.version import LooseVersion as LV
from calm.dsl.store import Version

from calm.dsl.log import get_logging_handle
from calm.dsl.cli import runbooks, bps
from calm.dsl.cli import scheduler
from calm.dsl.config import get_context
from calm.dsl.constants import CACHE
from calm.dsl.store import Cache
from calm.dsl.api import get_api_client
from calm.dsl.cli.constants import JOBINSTANCES

LOG = get_logging_handle(__name__)

DSL_SCHEDULER_FILE = [
    "job_create_one_time.py",
    "job_create_recurring.py",
    "job_unicode.py",
    "invalid_schedule_recurring.py",
]
DSL_INVALID_SCHEDULER_FILE = [
    "invalid_end_date_recurring.py",
    "expiry_less_currentdate_recurring.py",
    "execution_time_invalid_onetime.py",
    "invalid_cron_recurring.py",
    "start_greater_expiry_date_recurring.py",
]
DSL_RUNBOOK_FILE = "default_target_runbook.py"
DSL_BP_FILE = "example_blueprint.py"

# calm_version
CALM_VERSION = Version.get_version("Calm")


@pytest.mark.skipif(
    LV(CALM_VERSION) < LV("3.4.0"), reason="Scheduler FEAT is for v3.4.0"
)
class TestSchedulerCommands:
    @pytest.mark.scheduler
    @pytest.mark.parametrize(
        "dsl_file", ["job_app_action_recc.py", "job_app_action_onetime.py"]
    )
    def test_job_create_app_action(self, dsl_file):
        """
        Test for job create
        """
        current_path = os_lib.path.dirname(os_lib.path.realpath(__file__))
        dsl_file = os_lib.path.dirname(current_path) + "/scheduler/" + dsl_file
        LOG.info("Scheduler py file used {}".format(dsl_file))
        # Create blueprint
        current_path = os_lib.path.dirname(os_lib.path.realpath(__file__))
        dsl_file_name = dsl_file[dsl_file.rfind("/") :].replace("/", "")
        bp_name = dsl_file_name[: dsl_file_name.find(".")]

        bp_file = os_lib.path.dirname(current_path) + "/scheduler/" + DSL_BP_FILE
        client = get_api_client()
        bps.create_blueprint_from_dsl(client, bp_file, bp_name, force_create=True)
        # Launch Blueprint
        bps.launch_blueprint_simple(bp_name, app_name=bp_name, patch_editables=False)

        jobname = "test_job_scheduler" + str(uuid.uuid4())
        result = scheduler.create_job_command(dsl_file, jobname, None, False)
        assert result.get("resources").get("state") == "ACTIVE"

        time.sleep(140)
        result = json.loads(
            scheduler.get_job_instances_command(jobname, "json", None, 20, 0, False)
        )

        # If the job in One Time
        if "one_time_scheduler" in dsl_file:
            assert len(result) == 1
            state = result[0]["resources"]["state"]
            assert state != JOBINSTANCES.STATES.FAILED
        # If the job is RECURRING
        else:
            assert len(result) >= 1
            for record in result:
                assert record["resources"]["state"] != JOBINSTANCES.STATES.FAILED

    @pytest.mark.scheduler
    @pytest.mark.parametrize("dsl_file", DSL_SCHEDULER_FILE)
    def test_job_create_runbook(self, dsl_file):
        """
        Test for job create
        """
        current_path = os_lib.path.dirname(os_lib.path.realpath(__file__))
        dsl_file = os_lib.path.dirname(current_path) + "/scheduler/" + dsl_file
        LOG.info("Scheduler py file used {}".format(dsl_file))
        # Create runbook
        current_path = os_lib.path.dirname(os_lib.path.realpath(__file__))
        dsl_file_name_for_runbook = dsl_file[dsl_file.rfind("/") :].replace("/", "")
        runbook_name = dsl_file_name_for_runbook[: dsl_file_name_for_runbook.find(".")]
        runbook_file = (
            os_lib.path.dirname(current_path) + "/scheduler/" + DSL_RUNBOOK_FILE
        )

        runbooks.create_runbook_command(
            runbook_file, runbook_name, description="", force=True
        )

        result = scheduler.create_job_command(dsl_file, None, None, False)
        LOG.info(result)
        assert result.get("resources").get("state") == "ACTIVE"

    @pytest.mark.scheduler
    @pytest.mark.parametrize("dsl_file", DSL_INVALID_SCHEDULER_FILE)
    def test_invalid_job_create_runbook(self, dsl_file):
        """
        This covers job create scenario if invalid job start time is less than current time.
        """
        current_path = os_lib.path.dirname(os_lib.path.realpath(__file__))
        dsl_file = os_lib.path.dirname(current_path) + "/scheduler/" + dsl_file
        LOG.info("Scheduler py file used {}".format(dsl_file))
        # Create runbook
        current_path = os_lib.path.dirname(os_lib.path.realpath(__file__))
        dsl_file_name_for_runbook = dsl_file[dsl_file.rfind("/") :].replace("/", "")
        runbook_name = dsl_file_name_for_runbook[: dsl_file_name_for_runbook.find(".")]
        runbook_file = (
            os_lib.path.dirname(current_path) + "/scheduler/" + DSL_RUNBOOK_FILE
        )

        runbooks.create_runbook_command(
            runbook_file, runbook_name, description="", force=True
        )

        result = scheduler.create_job_command(dsl_file, None, None, False)
        LOG.info(result)
        assert result.get("resources").get("state") == "INACTIVE"
        msg_list = result.get("resources").get("message_list", [])
        msgs = []
        for msg_dict in msg_list:
            msgs.append(msg_dict.get("message", ""))

        # if expiry time less than current time
        if "test_invalid_end_date_recurring" in dsl_file:
            assert (
                "Please specify a valid expiry time, expiry time provided is less than current time"
                in msgs
            )

        # if expiry time less than current time
        elif "execution_time_invalid_onetime" in dsl_file:
            assert (
                "Please specify a valid execution time, execution time provided is less than current time"
                in msgs
            )

        elif "invalid_cron_recurring" in dsl_file:
            assert "Please specify a valid schedule for the recurring job" in msgs

        elif "start_greater_expiry_date_recurring" in dsl_file:
            assert "Please specify a start time less than expiry time" in msgs

        elif "expiry_less_currentdate_recurring" in dsl_file:
            assert (
                "Please specify a valid expiry time, expiry time provided is less than current time"
                in msgs
            )
            assert "Please specify a start time less than expiry time" in msgs

    @pytest.mark.scheduler
    @pytest.mark.parametrize("dsl_file", ["job_create_duplicate_name.py"])
    def test_job_create_duplicate_name(self, dsl_file):
        """
        Test for job create with duplicate names
        """
        current_path = os_lib.path.dirname(os_lib.path.realpath(__file__))
        dsl_file = os_lib.path.dirname(current_path) + "/scheduler/" + dsl_file
        LOG.info("Scheduler py file used {}".format(dsl_file))
        # Create runbook
        current_path = os_lib.path.dirname(os_lib.path.realpath(__file__))
        dsl_file_name_for_runbook = dsl_file[dsl_file.rfind("/") :].replace("/", "")
        runbook_name = dsl_file_name_for_runbook[: dsl_file_name_for_runbook.find(".")]
        runbook_file = (
            os_lib.path.dirname(current_path) + "/scheduler/" + DSL_RUNBOOK_FILE
        )

        runbooks.create_runbook_command(
            runbook_file, runbook_name, description="", force=True
        )
        jobname = "duplicate_name_check" + str(uuid.uuid4())
        # Create first job.
        result = scheduler.create_job_command(dsl_file, jobname, None, False)
        LOG.info(result)
        assert result.get("resources").get("state") == "ACTIVE"

        # Create second job with the same name as first one.
        result = scheduler.create_job_command(dsl_file, jobname, None, False)
        LOG.info(result)

        assert result.get("code", "") == 422

        msg_list = result.get("message_list", [])
        msgs = []
        for msg_dict in msg_list:
            msgs.append(msg_dict.get("details", "").get("error", ""))

        assert "job with name '{}' already exists".format(jobname) in msgs

    @pytest.mark.scheduler
    @pytest.mark.parametrize("dsl_file", ["job_create_blank_name.py"])
    def test_job_name_blank(self, dsl_file):
        """
        Test for job create with blank name
        """
        current_path = os_lib.path.dirname(os_lib.path.realpath(__file__))
        dsl_file = os_lib.path.dirname(current_path) + "/scheduler/" + dsl_file
        LOG.info("Scheduler py file used {}".format(dsl_file))

        # Create runbook
        dsl_file_name_for_runbook = dsl_file[dsl_file.rfind("/") :].replace("/", "")
        runbook_name = dsl_file_name_for_runbook[: dsl_file_name_for_runbook.find(".")]
        runbook_file = (
            os_lib.path.dirname(current_path) + "/scheduler/" + DSL_RUNBOOK_FILE
        )

        runbooks.create_runbook_command(
            runbook_file, runbook_name, description="", force=True
        )

        result = _create_job_with_custom_name(dsl_file)
        assert result.get("resources").get("state") == "INACTIVE"
        msg_list = result.get("resources").get("message_list", [])
        msgs = []
        for msg_dict in msg_list:
            msgs.append(msg_dict.get("message", ""))

        assert "Please specify a name for the schedule" in msgs

    @pytest.mark.scheduler
    @pytest.mark.parametrize("dsl_file", ["job_list.py"])
    def test_job_list(self, dsl_file):
        """
        Test for job LIST
        """
        current_path = os_lib.path.dirname(os_lib.path.realpath(__file__))
        dsl_file = os_lib.path.dirname(current_path) + "/scheduler/" + dsl_file
        LOG.info("Scheduler py file used {}".format(dsl_file))
        # Create runbook
        current_path = os_lib.path.dirname(os_lib.path.realpath(__file__))
        dsl_file_name_for_runbook = dsl_file[dsl_file.rfind("/") :].replace("/", "")
        runbook_name = dsl_file_name_for_runbook[: dsl_file_name_for_runbook.find(".")]
        runbook_file = (
            os_lib.path.dirname(current_path) + "/scheduler/" + DSL_RUNBOOK_FILE
        )

        runbooks.create_runbook_command(
            runbook_file, runbook_name, description="", force=True
        )

        job_name = "test_job_list_" + str(uuid.uuid4())
        result = _create_job_with_custom_name(dsl_file, job_name)
        LOG.info(result)
        assert result.get("resources").get("state") == "ACTIVE"

        result = scheduler.get_job_list_command(None, None, 20, 0, False, False)
        LOG.info(result)
        if job_name not in result.get_string():
            pytest.fail(
                "Job List API did not return the job which was created as part of the test"
            )

    @pytest.mark.scheduler
    @pytest.mark.parametrize("dsl_file", ["job_describe.py"])
    def test_job_describe(self, dsl_file):
        """
        Test for job GET
        """
        current_path = os_lib.path.dirname(os_lib.path.realpath(__file__))
        dsl_file = os_lib.path.dirname(current_path) + "/scheduler/" + dsl_file
        LOG.info("Scheduler py file used {}".format(dsl_file))
        # Create runbook
        current_path = os_lib.path.dirname(os_lib.path.realpath(__file__))
        dsl_file_name_for_runbook = dsl_file[dsl_file.rfind("/") :].replace("/", "")
        runbook_name = dsl_file_name_for_runbook[: dsl_file_name_for_runbook.find(".")]
        runbook_file = (
            os_lib.path.dirname(current_path) + "/scheduler/" + DSL_RUNBOOK_FILE
        )

        runbooks.create_runbook_command(
            runbook_file, runbook_name, description="", force=True
        )
        job_name = "test_job_describe_" + str(uuid.uuid4())
        result = _create_job_with_custom_name(dsl_file, job_name)
        LOG.info(result)
        assert result.get("resources").get("state") == "ACTIVE"

        client = get_api_client()
        job_get_res = scheduler.get_job(client, job_name, all=True)
        res, err = client.job.read(job_get_res["metadata"]["uuid"])
        job_response = res.json()
        LOG.info(job_response)
        assert job_response["resources"]["name"] == job_name

    @pytest.mark.scheduler
    @pytest.mark.parametrize(
        "dsl_file, dsl_runbook_file",
        [
            ("one_time_scheduler.py", "runbook_variables.py"),
            ("job_recurring_every_two_minute.py", "runbook_variables.py"),
            ("one_time_scheduler_decision_task.py", "decision_task.py"),
            ("job_recurring_every_two_minute_decision_task.py", "decision_task.py"),
        ],
    )
    def test_job_scheduler(self, dsl_file, dsl_runbook_file):
        """
        Test for job scheduler
        """
        current_path = os_lib.path.dirname(os_lib.path.realpath(__file__))
        dsl_file = os_lib.path.dirname(current_path) + "/scheduler/" + dsl_file
        LOG.info("Scheduler py file used {}".format(dsl_file))
        # Create runbook
        current_path = os_lib.path.dirname(os_lib.path.realpath(__file__))
        dsl_file_name_for_runbook = dsl_file[dsl_file.rfind("/") :].replace("/", "")
        runbook_name = dsl_file_name_for_runbook[: dsl_file_name_for_runbook.find(".")]
        runbook_file = (
            os_lib.path.dirname(current_path) + "/scheduler/" + dsl_runbook_file
        )

        runbooks.create_runbook_command(
            runbook_file, runbook_name, description="", force=True
        )
        jobname = "test_job_scheduler" + str(uuid.uuid4())
        result = scheduler.create_job_command(dsl_file, jobname, None, False)
        assert result.get("resources").get("state") == "ACTIVE"

        time.sleep(160)
        result = json.loads(
            scheduler.get_job_instances_command(jobname, "json", None, 20, 0, False)
        )

        # If the job in One Time
        if "one_time_scheduler" in dsl_file:
            assert len(result) == 1
            state = result[0]["resources"]["state"]
            assert state != JOBINSTANCES.STATES.FAILED
        # If the job is RECURRING
        else:
            assert len(result) >= 1
            for record in result:
                assert record["resources"]["state"] != JOBINSTANCES.STATES.FAILED


# To create job by passing a custom job name
def _create_job_with_custom_name(dsl_file, name=""):
    job_payload = scheduler.compile_job(dsl_file)
    job_payload["resources"]["name"] = name
    job_payload["metadata"]["name"] = name
    LOG.info(job_payload)

    ContextObj = get_context()
    project_config = ContextObj.get_project_config()
    project_name = project_config["name"]
    project_cache_data = Cache.get_entity_data(
        entity_type=CACHE.ENTITY.PROJECT, name=project_name
    )

    if not project_cache_data:
        LOG.error(
            "Project {} not found. Please run: calm update cache".format(project_name)
        )

    project_uuid = project_cache_data.get("uuid", "")
    job_payload["metadata"]["project_reference"] = {
        "kind": "project",
        "uuid": project_uuid,
        "name": project_name,
    }

    res, err = scheduler.create_job(job_payload)
    result = res.json()

    LOG.info(result)

    return result
