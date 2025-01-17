from datetime import datetime, timedelta
from pytz import timezone, utc

from calm.dsl.builtins import Job, JobScheduler

start_date = datetime.now() + timedelta(seconds=120)
start_date = (
    str(start_date.strftime("%Y-%m-%dT%H:%M:%SZ")).replace("T", " ").replace("Z", "")
)

expiry_date = datetime.now() + timedelta(seconds=600)
expiry_date = (
    str(expiry_date.strftime("%Y-%m-%dT%H:%M:%SZ")).replace("T", " ").replace("Z", "")
)

# Get the current time in UTC and Asia/Calcutta
utc_now = datetime.now(utc)
ist_time = utc_now.astimezone(timezone("Asia/Calcutta"))

# Compare offsets
local_offset = utc_now.utcoffset()  # Local UTC offset
ist_offset = ist_time.utcoffset()

if local_offset == utc.utcoffset(None):
    time_zone = "UTC"
elif local_offset == ist_offset:
    time_zone = "Asia/Calcutta"

APP_NAME = "job_app_action_recc"


class JobRecurring(Job):
    """Recurring Job for Executing an App Action"""

    name = "test_job_app_action_recc"
    schedule_info = JobScheduler.ScheduleInfo.recurring(
        "*/2 * * * *", start_date, expiry_date, time_zone
    )
    executable = JobScheduler.Exec.app_action(APP_NAME, "sample_profile_action")
