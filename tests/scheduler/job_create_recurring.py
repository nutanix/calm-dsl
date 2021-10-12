import uuid
from calm.dsl.builtins import Job
from calm.dsl.cli.scheduler import JobScheduler

start_date_time = "2050-10-08 16:17:15"
expiry_date_time = "2050-10-09 00:17:00"
cron = "52 15 * * *"
time_zone = "America/Jamaica"


class JobRecurringSpec(Job):
    """Recurring Job for Executing a Runbook"""

    name = "test_job_recurring" + str(uuid.uuid4())
    schedule_info = JobScheduler.ScheduleInfo.recurring(
        cron, start_date_time, expiry_date_time, time_zone
    )
    executable = JobScheduler.Exec.runbook("job_create_recurring", False)
