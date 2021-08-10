from datetime import datetime, timedelta

from calm.dsl.builtins import Job
from calm.dsl.cli.scheduler import JobScheduler

start_date = datetime.utcnow() + timedelta(seconds=120)
start_date = str(start_date.strftime("%Y-%m-%dT%H:%M:%SZ"))


class JobOneTime(Job):
    """One Time Job for Executing a Runbook"""

    name = "test_job"
    schedule_info = JobScheduler.ScheduleInfo.oneTime(start_date)
    executable = JobScheduler.Exec.runbook("runbook1")
