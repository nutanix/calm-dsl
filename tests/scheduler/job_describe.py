from calm.dsl.builtins import Job
from calm.dsl.cli.scheduler import JobScheduler


class JobRecurringSpec(Job):
    """Recurring Job for Executing a Runbook"""

    schedule_info = JobScheduler.ScheduleInfo.recurring(
        "15 1 1 * *", "2050-05-12T12:10:19Z", "2050-05-14T12:10:19Z"
    )
    executable = JobScheduler.Exec.runbook("job_describe", "")
