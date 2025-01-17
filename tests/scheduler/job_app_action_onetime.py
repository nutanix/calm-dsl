from datetime import datetime, timedelta
from pytz import timezone, utc

from calm.dsl.builtins import Job, JobScheduler

start_date = datetime.now() + timedelta(seconds=120)
start_date = (
    str(start_date.strftime("%Y-%m-%dT%H:%M:%SZ")).replace("T", " ").replace("Z", "")
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

APP_NAME = "job_app_action_onetime"


class JobOneTimeSpec(Job):
    """One Time Job for Executing an App Action"""

    schedule_info = JobScheduler.ScheduleInfo.oneTime(start_date, time_zone)
    executable = JobScheduler.Exec.app_action(APP_NAME, "sample_profile_action")
