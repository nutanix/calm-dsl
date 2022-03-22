import click

from calm.dsl.log import get_logging_handle

from .main import (
    library_get,
    library_import,
    library_create,
    library_describe,
    library_delete,
)
from .library_tasks import (
    get_tasks_list,
    describe_task,
    delete_task,
    create_task,
    import_task,
)

LOG = get_logging_handle(__name__)


@library_get.command("tasks")
@click.option(
    "--name", "-n", default=None, help="Search for task from task library by name"
)
@click.option(
    "--filter",
    "filter_by",
    "-f",
    default=None,
    help="Filter tasks from task library by this string",
)
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-o", default=0, help="Offset results by the specified amount"
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    default=False,
    help="Show only task from task library names.",
)
@click.option(
    "--all-items", "-a", is_flag=True, help="Get all items, including deleted ones"
)
def _get_tasks_list(name, filter_by, limit, offset, quiet, all_items):
    """Get the task from task library, optionally filtered by a string"""

    get_tasks_list(name, filter_by, limit, offset, quiet, all_items)


@library_describe.command("task")
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
    """Describe a task from task library"""

    describe_task(task_name, out)


@library_delete.command("task")
@click.argument("task_names", nargs=-1)
def _delete_task(task_names):
    """Deletes a task from task library"""

    delete_task(task_names)


@library_import.command("task")
@click.option(
    "--file",
    "-f",
    "task_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of task file (.json, .sh, .escript, .ps1)",
)
@click.option("--name", "-n", default=None, help="Task Library item name (Optional)")
@click.option(
    "--description", "-d", default=None, help="Task Library description (Optional)"
)
@click.option(
    "--out-vars",
    "-v",
    "out_vars",
    default=None,
    help="Set-variable output variables coma seperated (,) (Optional)",
)
@click.option(
    "--force",
    "-fc",
    is_flag=True,
    default=False,
    help="Updates existing task library item with the same name.",
)
def _import_task(task_file, name, description, out_vars, force):

    """Import task library item.

    (-f | --file) supports:\n

    \t.sh       - Shell script file\n
    \t.escript  - Escript file\n
    \t.ps1      - Powershell Script File\n

    Note:\n
        To import Set-Variable task, use --out-vars="OUT1,OUT2".

    Examples:\n
    calm import library task --name="Install IIS" -f Install_IIS.ps1\n
    calm import library task -f Install_Docker.sh\n
    calm import library task -f Install_Docker.sh --out-vars="IP_ADDRESS,PORT" """

    import_task(task_file, name, description, out_vars, force)


@library_create.command("task")
@click.option(
    "--file",
    "-f",
    "task_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of task file (.py/.json)",
)
@click.option("--name", "-n", default=None, help="Task Library item name (Optional)")
@click.option(
    "--description", "-d", default=None, help="Task Library description (Optional)"
)
@click.option(
    "--force",
    "-fc",
    is_flag=True,
    default=False,
    help="Updates existing task library item with the same name.",
)
def _create_task(task_file, name, description, force):

    """Create task library item.

    (-f | --file) supports:\n
    \t.py       - Python DSL\n
    \t.json     - Full json payload download from Calm API (v3 #GET) or using `calm describe library task <task_name> -o json `\n

    Examples:\n
    calm create library task --name=HTTPGetVM -f HTTPGetVM.py\n
    calm create library task -f HTTPGetVM.json\n"""

    create_task(task_file, name, description, force)
