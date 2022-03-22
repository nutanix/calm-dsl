import uuid

from calm.dsl.builtins import Job, JobScheduler

start_date_time = "2050-10-08 16:17:15"
time_zone = "America/Jamaica"

RUNBOOK_NAME = "job_create_one_time"


class JobOneTimeSpec(Job):
    """One Time Job for Executing a Runbook"""

    name = "test_job" + str(uuid.uuid4())[:8]
    schedule_info = JobScheduler.ScheduleInfo.oneTime(start_date_time, time_zone)
    executable = JobScheduler.Exec.runbook(RUNBOOK_NAME, False)
