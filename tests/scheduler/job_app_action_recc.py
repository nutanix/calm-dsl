from datetime import datetime, timedelta
from pytz import utc

from calm.dsl.builtins import Job, JobScheduler

start_date = datetime.now(utc) + timedelta(seconds=120)
start_date = (
    str(start_date.strftime("%Y-%m-%dT%H:%M:%SZ")).replace("T", " ").replace("Z", "")
)

expiry_date = datetime.now(utc) + timedelta(seconds=600)
expiry_date = (
    str(expiry_date.strftime("%Y-%m-%dT%H:%M:%SZ")).replace("T", " ").replace("Z", "")
)

time_zone = "UTC"

APP_NAME = "job_app_action_recc"


class JobRecurring(Job):
    """Recurring Job for Executing an App Action"""

    name = "test_job_app_action_recc"
    schedule_info = JobScheduler.ScheduleInfo.recurring(
        "*/2 * * * *", start_date, expiry_date, time_zone
    )
    executable = JobScheduler.Exec.app_action(APP_NAME, "sample_profile_action")
