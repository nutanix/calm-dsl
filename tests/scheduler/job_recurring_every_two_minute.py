import uuid

from datetime import datetime, timedelta

from calm.dsl.builtins import Job
from calm.dsl.cli.scheduler import JobScheduler

start_date = datetime.utcnow() + timedelta(seconds=10)
start_date = str(start_date.strftime("%Y-%m-%dT%H:%M:%SZ"))

expiry_date = datetime.utcnow() + timedelta(seconds=600)
expiry_date = str(expiry_date.strftime("%Y-%m-%dT%H:%M:%SZ"))


class JobRecurring(Job):
    """Recurring Job for Executing a Runbook"""

    schedule_info = JobScheduler.ScheduleInfo.recurring(
        "*/2 * * * *", start_date, expiry_date
    )
    executable = JobScheduler.Exec.runbook("job_recurring_every_two_minute", "")
