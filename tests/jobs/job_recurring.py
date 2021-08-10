from datetime import datetime, timedelta

from calm.dsl.builtins import Job
from calm.dsl.cli.scheduler import JobScheduler

start_date = datetime.utcnow() + timedelta(seconds=120)
start_date = str(start_date.strftime("%Y-%m-%dT%H:%M:%SZ"))

expiry_date = datetime.utcnow() + timedelta(seconds=600)
expiry_date = str(expiry_date.strftime("%Y-%m-%dT%H:%M:%SZ"))


class JobRecurring(Job):
    """Recurring Job for Executing a Runbook"""

    name = "test_job_recurring"
    schedule_info = JobScheduler.ScheduleInfo.recurring(
        "15 1 1 * *", start_date, expiry_date
    )
    executable = JobScheduler.Exec.runbook("runbook1")
