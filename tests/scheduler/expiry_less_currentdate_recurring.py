import uuid

from calm.dsl.builtins import Job
from calm.dsl.cli.scheduler import JobScheduler
from datetime import datetime, timedelta

start_time = datetime.utcnow() + timedelta(seconds=600)
start_time = str(start_time.strftime("%Y-%m-%dT%H:%M:%SZ"))

expiry_time = datetime.utcnow() - timedelta(seconds=600)
expiry_time = str(expiry_time.strftime("%Y-%m-%dT%H:%M:%SZ"))


class JobInvalidRecurringSpec(Job):
    """Recurring Invalid Job for Executing a Runbook with expiry date less than current date"""

    name = "test_job_invalid_recurring" + str(uuid.uuid4())
    schedule_info = JobScheduler.ScheduleInfo.recurring(
        "15 1 1 * *", start_time, expiry_time
    )
    executable = JobScheduler.Exec.runbook("expiry_less_currentdate_recurring", "")
