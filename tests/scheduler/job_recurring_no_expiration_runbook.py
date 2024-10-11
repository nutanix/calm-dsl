from datetime import datetime, timedelta

from calm.dsl.builtins import Job, JobScheduler

start_date = datetime.now() + timedelta(seconds=120)
start_date = (
    str(start_date.strftime("%Y-%m-%dT%H:%M:%SZ")).replace("T", " ").replace("Z", "")
)
cron = "50 23 * * *"
time_zone = "UTC"

RUNBOOK_NAME = "job_recurring_no_expiration_runbook"


class JobRecurring(Job):
    """
    Recurring job with no expiration to execute runbook.
    Note: Skip passing expiry_time parameter to set no expiration in job.
    """

    name = "test_no_expiration_rb_job"
    schedule_info = JobScheduler.ScheduleInfo.recurring(
        cron, start_date, time_zone=time_zone
    )

    executable = JobScheduler.Exec.runbook(RUNBOOK_NAME, False)
