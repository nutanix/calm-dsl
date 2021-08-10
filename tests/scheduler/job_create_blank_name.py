from calm.dsl.builtins import Job
from calm.dsl.cli.scheduler import JobScheduler


class JobOneTimeBlankNameSpec(Job):
    """One Time Job for Executing a Runbook"""

    schedule_info = JobScheduler.ScheduleInfo.oneTime("2050-05-12T14:10:19Z")
    executable = JobScheduler.Exec.runbook("job_create_blank_name", "")
