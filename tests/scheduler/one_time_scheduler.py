from datetime import datetime, timedelta

from calm.dsl.builtins import Job
from calm.dsl.cli.scheduler import JobScheduler

start_date = datetime.now() + timedelta(seconds=10)
start_date = (
    str(start_date.strftime("%Y-%m-%dT%H:%M:%SZ")).replace("T", " ").replace("Z", "")
)
time_zone = "Asia/Kolkata"

RUNBOOK_NAME = "one_time_scheduler"


class JobOneTimeSpec(Job):
    """One Time Job for Executing a Runbook"""

    schedule_info = JobScheduler.ScheduleInfo.oneTime(start_date, time_zone)
    executable = JobScheduler.Exec.runbook(RUNBOOK_NAME, False)
