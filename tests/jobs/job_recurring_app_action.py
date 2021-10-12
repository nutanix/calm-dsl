from datetime import datetime, timedelta

from calm.dsl.builtins import Job
from calm.dsl.cli.scheduler import JobScheduler

start_date_time = "2021-10-08 16:17:15"
expiry_date_time = "2021-10-09 00:17:00"
cron = "52 15 * * *"
time_zone = "America/Jamaica"


class JobRecurring(Job):
    """Recurring Job for Executing Snapshot action of app"""

    name = "job_app_action_recc"
    schedule_info = JobScheduler.ScheduleInfo.recurring(
        cron, start_date_time, expiry_date_time, time_zone=time_zone
    )
    executable = JobScheduler.Exec.app_action("ahv app 1", "Snapshot_snap2")
