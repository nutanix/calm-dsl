import uuid

from calm.dsl.builtins import Job
from calm.dsl.cli.scheduler import JobScheduler

start_date_time = "2020-10-08 16:17:15"
time_zone = "America/Jamaica"


class JobOneTimeSpec(Job):
    """One Time Invalid Job for Executing a Runbook with execution date less than current date"""

    name = "test_job_" + str(uuid.uuid4())
    schedule_info = JobScheduler.ScheduleInfo.oneTime(start_date_time, time_zone)
    executable = JobScheduler.Exec.runbook("execution_time_invalid_onetime", False)