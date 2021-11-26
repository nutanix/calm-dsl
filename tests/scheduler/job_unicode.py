import uuid
from datetime import datetime, timedelta

from calm.dsl.builtins import Job
from calm.dsl.cli.scheduler import JobScheduler

start_date_time = "2050-10-08 16:17:15"
expiry_date_time = "2050-10-09 00:17:00"
cron = "52 15 * * *"
time_zone = "America/Jamaica"


class JobInvalidRecurringSpec(Job):
    """Recurring Job with Unicode кызмат"""

    name = "test_unicode_кызмат_" + str(uuid.uuid4())[:8]
    schedule_info = JobScheduler.ScheduleInfo.recurring(
        cron, start_date_time, expiry_date_time, time_zone
    )
    executable = JobScheduler.Exec.runbook("job_unicode", False)
