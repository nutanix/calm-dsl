import uuid

from calm.dsl.builtins import Job
from calm.dsl.cli.scheduler import JobScheduler

start_date_time = "2020-10-08 16:17:15"
expiry_date_time = "2050-10-09 00:17:00"
cron = "52 15 * * *"
time_zone = "America/Jamaica"


class JobInvalidRecurringSpec(Job):
    """Recurring Invalid Job for Executing a Runbook with start date less than current date"""

    name = "test_job_invalid_recurring_" + str(uuid.uuid4())
    schedule_info = JobScheduler.ScheduleInfo.recurring(
        cron, start_date_time, expiry_date_time, time_zone
    )
    executable = JobScheduler.Exec.runbook("invalid_schedule_recurring", False)
