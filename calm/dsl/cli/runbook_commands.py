import click

from calm.dsl.log import get_logging_handle

from .main import (
    compile,
    get,
    describe,
    delete,
    run,
    create,
    update,
    format,
    watch,
    pause,
    resume,
    abort,
)
from .runbooks import (
    get_runbook_list,
    create_runbook_command,
    update_runbook_command,
    get_execution_history,
    run_runbook_command,
    describe_runbook,
    delete_runbook,
    format_runbook_command,
    compile_runbook_command,
    watch_runbook_execution,
    resume_runbook_execution,
    pause_runbook_execution,
    abort_runbook_execution,
)

LOG = get_logging_handle(__name__)


@get.command("runbooks", feature_min_version="3.0.0", experimental=True)
@click.option("--name", "-n", default=None, help="Search for runbooks by name")
@click.option(
    "--filter", "filter_by", "-f", default=None, help="Filter runbooks by this string"
)
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-o", default=0, help="Offset results by the specified amount"
)
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only runbook names."
)
@click.option(
    "--all-items", "-a", is_flag=True, help="Get all items, including deleted ones"
)
def _get_runbook_list(name, filter_by, limit, offset, quiet, all_items):
    """Get the runbooks, optionally filtered by a string"""

    get_runbook_list(name, filter_by, limit, offset, quiet, all_items)


@get.command("runbook_executions", feature_min_version="3.0.0", experimental=True)
@click.option(
    "--name",
    "-n",
    default=None,
    help="Search for previous runbook runs by name of runbook (Optional)",
)
@click.option(
    "--filter",
    "filter_by",
    "-f",
    default=None,
    help="Filter previous runbook executions by this string",
)
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-o", default=0, help="Offset results by the specified amount"
)
def _get_execution_history(name, filter_by, limit, offset):
    """Get previous runbook executions, optionally filtered by a string"""

    get_execution_history(name, filter_by, limit, offset)


@create.command("runbook", feature_min_version="3.0.0", experimental=True)
@click.option(
    "--file",
    "-f",
    "runbook_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of Runbook file to upload",
)
@click.option("--name", "-n", default=None, help="Runbook name (Optional)")
@click.option("--description", default=None, help="Runbook description (Optional)")
@click.option(
    "--force",
    "-fc",
    is_flag=True,
    default=False,
    help="Deletes existing blueprint with the same name before create.",
)
def _create_runbook_command(runbook_file, name, description, force):
    """Creates a runbook"""

    create_runbook_command(runbook_file, name, description, force)


@update.command("runbook", feature_min_version="3.0.0", experimental=True)
@click.option(
    "--file",
    "-f",
    "runbook_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of Runbook file to upload",
)
@click.option("--name", "-n", default=None, required=True, help="Runbook name")
@click.option("--description", default=None, help="Runbook description (Optional)")
def _update_runbook_command(runbook_file, name, description):
    """Updates a runbook"""

    update_runbook_command(runbook_file, name, description)


@delete.command("runbook", feature_min_version="3.0.0", experimental=True)
@click.argument("runbook_names", nargs=-1)
def _delete_runbook(runbook_names):
    """Deletes a runbook"""

    delete_runbook(runbook_names)


@describe.command("runbook", feature_min_version="3.0.0", experimental=True)
@click.argument("runbook_name")
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format [text|json].",
)
def _describe_runbook(runbook_name, out):
    """Describe a runbook"""

    describe_runbook(runbook_name, out)


@format.command("runbook", feature_min_version="3.0.0", experimental=True)
@click.option(
    "--file",
    "-f",
    "runbook_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of Runbook file to format",
)
def _format_runbook_command(runbook_file):
    format_runbook_command(runbook_file)


@compile.command("runbook", feature_min_version="3.0.0", experimental=True)
@click.option(
    "--file",
    "-f",
    "runbook_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of Runbook file to upload",
)
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="output format [json|yaml].",
)
def _compile_runbook_command(runbook_file, out):
    """Compiles a DSL (Python) runbook into JSON or YAML"""
    compile_runbook_command(runbook_file, out)


@run.command("runbook", feature_min_version="3.0.0", experimental=True)
@click.argument("runbook_name", required=False)
@click.option(
    "--file",
    "-f",
    "runbook_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=False,
    help="Path of Runbook file to directly run runbook",
)
@click.option(
    "--ignore_runtime_variables",
    "-i",
    is_flag=True,
    default=False,
    help="Ignore runtime variables and use defaults",
)
@click.option(
    "--input-file",
    "input_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=False,
    help="Path to python file for runtime editables",
)
@click.option("--watch/--no-watch", "-w", default=False, help="Watch scrolling output")
def _run_runbook_command(
    runbook_name, watch, ignore_runtime_variables, runbook_file=None, input_file=None
):
    """Execute the runbook given by name or runbook file. All runtime variables and default target will be prompted by default. When passing the 'ignore_runtime_editable' flag, no variables will be prompted and all default values will be used. The runbook  default values can be  overridden by passing a Python file via 'input_file'. When passing a Python file, no variables will be prompted.

    \b
    >: input_file: Python file consisting of variables 'variable_list' and 'default_target'
    Ex: variable_list = {
        "value": {"value": <Variable Value>},
        "name": "<Variable Name>"
    }
    default_target: <Endpoint Name>"""

    run_runbook_command(
        runbook_name,
        watch,
        ignore_runtime_variables,
        runbook_file=runbook_file,
        input_file=input_file,
    )


@watch.command("runbook_execution", feature_min_version="3.0.0", experimental=True)
@click.argument("runlog_uuid", required=True)
def _watch_runbook_execution(runlog_uuid):
    """Watch the runbook execution using given runlog UUID"""

    watch_runbook_execution(runlog_uuid)


@pause.command("runbook_execution", feature_min_version="3.0.0", experimental=True)
@click.argument("runlog_uuid", required=True)
def _pause_runbook_execution(runlog_uuid):
    """Pause the running runbook execution"""

    pause_runbook_execution(runlog_uuid)


@resume.command("runbook_execution", feature_min_version="3.0.0", experimental=True)
@click.argument("runlog_uuid", required=True)
def _resume_runbook_execution(runlog_uuid):
    """Resume the paused runbook execution"""

    resume_runbook_execution(runlog_uuid)


@abort.command("runbook_execution", feature_min_version="3.0.0", experimental=True)
@click.argument("runlog_uuid", required=True)
def _abort_runbook_execution(runlog_uuid):
    """Abort the runbook execution"""

    abort_runbook_execution(runlog_uuid)
