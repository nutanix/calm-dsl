# Scheduler

## CLI commands
- Create Job – `calm create job -f <path to job py file in scheluler> -n <job name>`
- List Jobs – `calm get jobs`
- Get Job Details - `calm describe job <job name>`
- Get Job Instances - `calm get job_instances <job name>`
- Delete Job – `calm delete job <job name>`

## Built-in Models

- Added `Job` model to create dsl-entity for defining job.

- Added `JobScheduler.ScheduleInfo.oneTime` helper for defining schedule info for one time job.

- Added `JobScheduler.ScheduleInfo.recurring` helper for defining schedule info for recurring job.

- Added `JobScheduler.Exec.runbook` helper for defining `runbook` as an executable object for job.

- Added `JobScheduler.Exec.app_action` helper for defining `application action` as an executable object for job.

## Sample examples:

### One-Time Job in Scheduler with Runbook as an executable.

- The Runbook `runbook_name` will be executed on March 08 2022 Asia/Calcutta.

        from calm.dsl.builtins import Job, JobScheduler

        start_date_time = "2022-03-08 19:14:00"
        time_zone = "Asia/Calcutta"


        class JobOneTime(Job):
            """One Time Job for Executing a Runbook"""

            name = "test_job"
            schedule_info = JobScheduler.ScheduleInfo.oneTime(
                start_date_time, time_zone=time_zone
            )
            executable = JobScheduler.Exec.runbook("runbook_name")

### Recurring Job in Scheduler with Application Action as an executable

- The Runbook `job_app_action_recc` will be executed from `2022-03-01 23:17:15` to `2022-03-05 00:17:00` at `11:50 PM`.

        from calm.dsl.builtins import Job, JobScheduler

        start_date_time = "2022-03-01 23:17:15"
        expiry_date_time = "2022-03-05 00:17:00"
        cron = "50 23 * * *"
        time_zone = "Asia/Calcutta"

        class JobRecurring(Job):
            """Recurring Job for Executing Snapshot action of app"""

            name = "job_app_action_recc"
            schedule_info = JobScheduler.ScheduleInfo.recurring(
                cron, start_date_time, expiry_date_time, time_zone=time_zone
            )
            executable = JobScheduler.Exec.app_action("app_name", "Restore Action")

### Recurring Job in Scheduler with non expiration Application Action as an executable

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

### Recurring Job in Scheduler with non expiration Runbook as an executable.

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

# Dynamic Credential

## CLI commands

- `calm get accounts --type=custom_provider`: Added command for listing out existing credential providers.
- `calm describe account <account name>`: Added support to display credential provider account info


## Builtin-Models

- Added `dynamic_cred` helper for defining dynamic cred entity in dsl file. User can use dynamic cred in `blueprints/runbooks/endpoints`.

        DefaultCred = dynamic_cred(
            DEFAULT_CRED_USERNAME,
            Ref.Account(name=CRED_PROVIDER),
            variable_dict={"path": SECRET_PATH},
            name="default cred",
            default=True,
        )

- Added `Provider.Custom_Provider` helper for defining custom provider object to be included in project-providers.

        class TestDemoProject(Project):
            """Test project"""

            providers = [
                Provider.Custom_Provider(
                    account=Ref.Account(ACCOUNT),
                )
            ]

# Cache
- Allow cache update for individual enities. CLI command: `calm update cache --entity [ahv_subnet|ahv_disk_image|account|project|environment|user|role|directory_service|user_group|ahv_network_function_chain|app_protection_policy]`
- Fixed issue [#184](https://github.com/nutanix/calm-dsl/issues/184). Allow atomic updates in cache for entity crud operations i.e. project/environment crud operations etc.

*** Please look for Calm 3.4.0 overview [here](https://drive.google.com/file/d/1oITux-OVntRQ3eh8v2h-dRfCEnqpxcOl/view?usp=sharing)
