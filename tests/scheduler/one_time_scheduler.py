from datetime import datetime, timedelta

from calm.dsl.builtins import Job
from calm.dsl.cli.scheduler import JobScheduler

start_date = datetime.utcnow() + timedelta(seconds=10)
start_date = str(start_date.strftime("%Y-%m-%dT%H:%M:%SZ"))


class JobOneTimeSpec(Job):
    """One Time Job for Executing a Runbook"""

    schedule_info = JobScheduler.ScheduleInfo.oneTime(start_date)
    executable = JobScheduler.Exec.runbook("one_time_scheduler", "")
