from calm.dsl.builtins import Job, JobScheduler

start_date_time = "2021-11-15 23:17:15"
expiry_date_time = "2021-11-16 00:17:00"
cron = "50 23 * * *"
time_zone = "Asia/Calcutta"


class JobRecurring(Job):
    """Recurring Job for Executing Snapshot action of app"""

    name = "job_app_action_recc"
    schedule_info = JobScheduler.ScheduleInfo.recurring(
        cron, start_date_time, expiry_date_time, time_zone=time_zone
    )
    executable = JobScheduler.Exec.app_action("snapshot check app", "Restore_ss")
