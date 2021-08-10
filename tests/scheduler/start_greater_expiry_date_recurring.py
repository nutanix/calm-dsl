import uuid

from calm.dsl.builtins import Job
from calm.dsl.cli.scheduler import JobScheduler


class JobInvalidRecurringSpec(Job):
    """Recurring Invalid Job for Executing a Runbook with start date greater than expiry date"""

    name = "test_job_invalid_recurring_" + str(uuid.uuid4())
    schedule_info = JobScheduler.ScheduleInfo.recurring(
        "15 1 1 * *", "2050-05-12T12:10:19Z", "2050-05-10T12:10:19Z"
    )
    executable = JobScheduler.Exec.runbook("start_greater_expiry_date_recurring", "")
