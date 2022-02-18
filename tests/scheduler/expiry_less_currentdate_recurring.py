import uuid

from calm.dsl.builtins import Job
from calm.dsl.cli.scheduler import JobScheduler
from datetime import datetime, timedelta

start_date_time = "2050-10-08 16:17:15"
expiry_date_time = "2020-10-09 00:17:00"
cron = "52 15 * * *"
time_zone = "America/Jamaica"


start_time = datetime.utcnow() + timedelta(seconds=600)
start_time = str(start_time.strftime("%Y-%m-%dT%H:%M:%SZ"))

expiry_time = datetime.utcnow() - timedelta(seconds=600)
expiry_time = str(expiry_time.strftime("%Y-%m-%dT%H:%M:%SZ"))


RUNBOOK_NAME = "expiry_less_currentdate_recurring"


class JobInvalidRecurringSpec(Job):
    """Recurring Invalid Job for Executing a Runbook with expiry date less than current date"""

    name = "test_job_invalid_recurring" + str(uuid.uuid4())[:8]
    schedule_info = JobScheduler.ScheduleInfo.recurring(
        cron, start_date_time, expiry_date_time, time_zone
    )
    executable = JobScheduler.Exec.runbook(RUNBOOK_NAME, False)
