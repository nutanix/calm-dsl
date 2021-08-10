import uuid

from calm.dsl.builtins import Job
from calm.dsl.cli.scheduler import JobScheduler


class JobOneTimeSpec(Job):
    """One Time Invalid Job for Executing a Runbook with execution date less than current date"""

    name = "test_job_" + str(uuid.uuid4())
    schedule_info = JobScheduler.ScheduleInfo.oneTime("2020-05-12T14:10:19Z")
    executable = JobScheduler.Exec.runbook("execution_time_invalid_onetime", "")
