from calm.dsl.builtins import Job, JobScheduler

start_date_time = "2021-11-08 19:14:00"
time_zone = "Asia/Calcutta"


class JobOneTime(Job):
    """One Time Job for Executing a Runbook"""

    name = "test_job"
    schedule_info = JobScheduler.ScheduleInfo.oneTime(
        start_date_time, time_zone=time_zone
    )
    executable = JobScheduler.Exec.runbook("job_recurring_every_two_minute")
