from datetime import datetime, timedelta

from calm.dsl.builtins import Job
from calm.dsl.cli.scheduler import JobScheduler

start_date = datetime.now() + timedelta(seconds=30)
start_date = (
    str(start_date.strftime("%Y-%m-%dT%H:%M:%SZ")).replace("T", " ").replace("Z", "")
)

time_zone = "Asia/Kolkata"

APP_NAME = "job_app_action_onetime"


class JobOneTimeSpec(Job):
    """One Time Job for Executing an App Action"""

    schedule_info = JobScheduler.ScheduleInfo.oneTime(start_date, time_zone)
    executable = JobScheduler.Exec.app_action(APP_NAME, "sample_profile_action")
