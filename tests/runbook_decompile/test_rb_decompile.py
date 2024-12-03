import os
import shutil
from click.testing import CliRunner
from calm.dsl.cli import main as cli
from calm.dsl.log import get_logging_handle
from calm.dsl.decompile.file_handler import get_runbook_dir

LOG = get_logging_handle(__name__)
RB_DIR = "tests/runbook_decompile/runbook_json"
RB_FILES = [
    "exec_rb.json",
    "set_variable.json",
    "delay.json",
    "http.json",
    "while.json",
    "decision.json",
    "vm_poweron.json",
    "vm_poweroff.json",
    "vm_restart.json",
    "task_tree_runbook.json",
    # "ndb_task.json",
    "fetch_http_var.json",
]


class TestRunbookDecompile:
    def teardown_method(self):
        dir_location = get_runbook_dir()
        shutil.rmtree(dir_location)

    def test_decompile_command(self):
        runner = CliRunner()
        rb_file_location = os.path.join(os.getcwd(), RB_DIR, RB_FILES[0])
        result = runner.invoke(cli, ["-vv", "decompile", "runbook"])
        assert (
            result.exit_code
        ), "expected runbook decompile to fail as no name or file location is specified, but passed."
        result = runner.invoke(
            cli, ["-vv", "decompile", "runbook", "abc", "-f", rb_file_location]
        )
        assert (
            result.exit_code
        ), "expected runbook decompile to fail as both name and file location is specified, but passed."
        result = runner.invoke(
            cli, ["-vv", "decompile", "runbook", "-f", rb_file_location]
        )
        assert not result.exit_code, "expected runbook decompile to work."

    def test_decompile(self):
        runner = CliRunner()
        for rb_file in RB_FILES:
            rb_file_location = os.path.join(os.getcwd(), RB_DIR, rb_file)
            LOG.info("decompiling runbook file at {}".format(rb_file_location))
            result = runner.invoke(
                cli, ["-vv", "decompile", "runbook", "-f", rb_file_location]
            )
            assert (
                not result.exit_code
            ), "runbook decompile expected to pass but failed for {}".format(rb_file)
