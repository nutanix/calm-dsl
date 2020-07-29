import click

from calm.dsl.log import get_logging_handle

from .main import (
    get,
    describe,
    delete,
)
from .tasks import (
    get_tasks_list,
    describe_task,
    delete_task
)

LOG = get_logging_handle(__name__)


@get.command("tasks", feature_min_version="3.0.0", experimental=True)
@click.option("--name", "-n", default=None, help="Search for task by name")
@click.option(
    "--filter", "filter_by", "-f", default=None, help="Filter tasks by this string"
)
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-o", default=0, help="Offset results by the specified amount"
)
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only task names."
)
@click.option(
    "--all-items", "-a", is_flag=True, help="Get all items, including deleted ones"
)
def _get_tasks_list(name, filter_by, limit, offset, quiet, all_items):
    """Get the tasks, optionally filtered by a string"""

    get_tasks_list(name, filter_by, limit, offset, quiet, all_items)


@describe.command("task", feature_min_version="3.0.0", experimental=True)
@click.argument("task_name")
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format",
)
def _describe_task(task_name, out):
    """Describe a task"""

    describe_task(task_name, out)


@delete.command("task", feature_min_version="3.0.0", experimental=True)
@click.argument("task_names", nargs=-1)
def _delete_task(task_names):
    """Deletes a task library items"""

    delete_task(task_names)