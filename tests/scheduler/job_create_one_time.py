import uuid

from calm.dsl.builtins import Job
from calm.dsl.cli.scheduler import JobScheduler


class JobOneTimeSpec(Job):
    """One Time Job for Executing a Runbook"""

    name = "test_job" + str(uuid.uuid4())
    schedule_info = JobScheduler.ScheduleInfo.oneTime("2050-05-12T14:10:19Z")
    executable = JobScheduler.Exec.runbook("job_create_one_time", "")
