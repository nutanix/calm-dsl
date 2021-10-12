import click

from calm.dsl.log import get_logging_handle

from .main import (
    create,
    describe,
    get,
    delete,
)
from .scheduler import (
    create_job_command,
    describe_job_command,
    get_job_list_command,
    get_job_instances_command,
    delete_job,
)

LOG = get_logging_handle(__name__)


@create.command("job", feature_min_version="3.0.0", experimental=True)
@click.option(
    "--file",
    "-f",
    "job_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="Path of Job file to upload",
)
@click.option("--name", "-n", default=None, help="Job name (Optional)")
@click.option("--description", default=None, help="Job description (Optional)")
@click.option(
    "--force",
    "-fc",
    is_flag=True,
    default=False,
    help="",
)
def _create_job_command(job_file, name, description, force):
    """Creates a job in scheduler"""

    create_job_command(job_file, name, description, force)


@describe.command("job", feature_min_version="3.0.0", experimental=True)
@click.argument("job_name")
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format [text|json].",
)
def _describe_job(job_name, out):
    """Describe a job"""

    describe_job_command(job_name, out)


@get.command("jobs", feature_min_version="3.0.0", experimental=True)
@click.option("--name", "-n", default=None, help="Search for job by name")
@click.option(
    "--filter", "filter_by", "-f", default=None, help="Filter jobs by this string"
)
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-o", default=0, help="Offset results by the specified amount"
)
@click.option("--quiet", "-q", is_flag=True, default=False, help="Show only job names.")
@click.option(
    "--all-items", "-a", is_flag=True, help="Get all items, including deleted ones"
)
def _get_job_list(name, filter_by, limit, offset, quiet, all_items):
    """Get the jobs, optionally filtered by a string"""

    get_job_list_command(name, filter_by, limit, offset, quiet, all_items)


@get.command("job_instances", feature_min_version="3.0.0", experimental=True)
@click.argument("job_name")
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format [text|json].",
)
@click.option(
    "--filter", "filter_by", "-f", default=None, help="Filter jobs by this string"
)
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-o", default=0, help="Offset results by the specified amount"
)
@click.option(
    "--all-items", "-a", is_flag=True, help="Get all items, including deleted ones"
)
def _get_job_instances(job_name, out, filter_by, limit, offset, all_items):
    """Describe a job"""

    get_job_instances_command(job_name, out, filter_by, limit, offset, all_items)


@delete.command("job")
@click.argument("job_names", nargs=-1)
def _delete_job(job_names):
    """Deletes a job"""

    delete_job(job_names)
