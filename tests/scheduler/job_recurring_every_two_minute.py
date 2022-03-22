from datetime import datetime, timedelta

from calm.dsl.builtins import Job, JobScheduler

start_date = datetime.now() + timedelta(seconds=10)
start_date = (
    str(start_date.strftime("%Y-%m-%dT%H:%M:%SZ")).replace("T", " ").replace("Z", "")
)

expiry_date = datetime.now() + timedelta(seconds=600)
expiry_date = (
    str(expiry_date.strftime("%Y-%m-%dT%H:%M:%SZ")).replace("T", " ").replace("Z", "")
)

time_zone = "Asia/Kolkata"

RUNBOOK_NAME = "job_recurring_every_two_minute"


class JobRecurring(Job):
    """Recurring Job for Executing a Runbook"""

    schedule_info = JobScheduler.ScheduleInfo.recurring(
        "*/2 * * * *", start_date, expiry_date, time_zone
    )
    executable = JobScheduler.Exec.runbook(RUNBOOK_NAME, False)
