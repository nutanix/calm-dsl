from calm.dsl.builtins import Job, JobScheduler

start_date_time = "2021-11-18 17:58:15"
time_zone = "Asia/Calcutta"


class JobOneTime(Job):
    """One Time Job for Executing an App Action"""

    name = "job_app_action_onetime"
    schedule_info = JobScheduler.ScheduleInfo.oneTime(
        start_date_time, time_zone=time_zone
    )
    executable = JobScheduler.Exec.app_action("Hadoop", "Stop")
