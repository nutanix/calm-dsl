For further details on Job scheduler refer [here](../../release-notes/3.4.0/README.md)

#### Recurring Job in Scheduler with non expiration Application Action as an executable

- The Runbook `test_no_expiration_app_job` will be executed from `2022-03-01 23:17:15` with no expiry time. 
- Skip passing expiry_time parameter to set no expiration in job.

        from calm.dsl.builtins import Job, JobScheduler

        start_date = "2022-03-01 23:17:15"
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

#### Recurring Job in Scheduler with non expiration Runbook as an executable.

- The Runbook `job_recurring_no_expiration_runbook` will be executed from March 08 2022 Asia/Calcutta with no expiry time.
- Skip passing expiry_time parameter to set no expiration in job.

        from calm.dsl.builtins import Job, JobScheduler

        start_date = "2022-03-08 19:14:00"
        cron = "50 23 * * *"
        time_zone = "Asia/Calcutta"

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