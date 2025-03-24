from datetime import datetime, timedelta
from pytz import utc

from calm.dsl.builtins import Job, JobScheduler

start_date = datetime.now(utc) + timedelta(seconds=10)
start_date = (
    str(start_date.strftime("%Y-%m-%dT%H:%M:%SZ")).replace("T", " ").replace("Z", "")
)

time_zone = "UTC"

RUNBOOK_NAME = "one_time_scheduler"


class JobOneTimeSpec(Job):
    """One Time Job for Executing a Runbook"""

    schedule_info = JobScheduler.ScheduleInfo.oneTime(start_date, time_zone)
    executable = JobScheduler.Exec.runbook(RUNBOOK_NAME, False)
