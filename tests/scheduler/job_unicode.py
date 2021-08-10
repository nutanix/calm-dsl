import uuid
from datetime import datetime, timedelta

from calm.dsl.builtins import Job
from calm.dsl.cli.scheduler import JobScheduler

start_time = datetime.now() + timedelta(seconds=120)
start_time = str(start_time.strftime("%Y-%m-%dT%H:%M:%SZ"))

expiry_time = datetime.now() + timedelta(seconds=600)
expiry_time = str(expiry_time.strftime("%Y-%m-%dT%H:%M:%SZ"))


class JobInvalidRecurringSpec(Job):
    """Recurring Job with Unicode кызмат"""

    name = "test_unicode_кызмат_" + str(uuid.uuid4())
    schedule_info = JobScheduler.ScheduleInfo.recurring(
        "15 1 1 * *", start_time, expiry_time
    )
    executable = JobScheduler.Exec.runbook("job_unicode", "")
