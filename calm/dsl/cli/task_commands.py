import click
import time

from .main import watch
from .constants import ERGON_TASK
from calm.dsl.api import get_api_client, get_resource_api
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def watch_task(task_uuid, poll_interval=2):

    client = get_api_client()
    Obj = get_resource_api("tasks", client.connection)

    cnt = 0
    while True:
        LOG.info("Fetching status of task")
        res, err = Obj.read(task_uuid)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        res = res.json()
        status = res["status"]
        LOG.info(status)

        if status in ERGON_TASK.TERMINAL_STATES:
            error_detail = res.get("error_detail", "")
            if error_detail:
                LOG.error(error_detail)
            return status

        time.sleep(poll_interval)
        cnt += 1
        if cnt == 10:
            break

    LOG.info(
        "Task couldn't reached to terminal state in {} seconds. Exiting...".format(
            poll_interval * 10
        )
    )


@watch.command("task")
@click.argument("task_uuid")
@click.option(
    "--poll_interval",
    "-p",
    type=int,
    default=2,
    show_default=True,
    help="Give polling interval",
)
def _watch_task(task_uuid, poll_interval):
    """Watch a task"""

    watch_task(task_uuid=task_uuid, poll_interval=poll_interval)
