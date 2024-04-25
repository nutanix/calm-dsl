from datetime import datetime, timedelta

from calm.dsl.builtins import Job, JobScheduler

start_date = datetime.now() + timedelta(seconds=10)
start_date = (
    str(start_date.strftime("%Y-%m-%dT%H:%M:%SZ")).replace("T", " ").replace("Z", "")
)
cron = "50 23 * * *"
time_zone = "Asia/Calcutta"

APP_NAME = "job_recurring_no_expiration_app_action"


class JobRecurring(Job):
    """
    Recurring Job with no expiration to Start action on app.
    Note: Skip passing expiry_time parameter to set no expiration in job.
    """

    name = "test_no_expiration_app_job"
    schedule_info = JobScheduler.ScheduleInfo.recurring(
        cron, start_date, time_zone=time_zone
    )

    executable = JobScheduler.Exec.app_action(APP_NAME, "Start")
