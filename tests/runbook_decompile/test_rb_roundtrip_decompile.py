import os
import json
import shutil
import uuid
import traceback
from click.testing import CliRunner
from calm.dsl.cli import main as cli
from calm.dsl.log import get_logging_handle
from calm.dsl.decompile.file_handler import get_runbook_dir


LOG = get_logging_handle(__name__)
RB_PY_FILE = "tests/runbook_decompile/runbook_py/runbook.py"
EP_FILE = "tests/runbook_decompile/endpoint/test_endpoint.json"


class TestRoundtripRunbookDecompile:
    def setup_method(self):
        self.created_rb_list = []
        self.rb_dir_list = []

    def teardown_method(self):
        for rb_name in self.created_rb_list:
            LOG.info("Deleting Runbook {}".format(rb_name))
            runner = CliRunner()
            result = runner.invoke(cli, ["delete", "runbook", rb_name])
            assert result.exit_code == 0

        for dir_location in self.rb_dir_list:
            shutil.rmtree(dir_location)

    def test_roundtrip_decompile(self):
        runner = CliRunner()
        rb_py_file_location = os.path.join(os.getcwd(), RB_PY_FILE)
        # compile original runbook
        result = runner.invoke(
            cli, ["-vv", "compile", "runbook", "-f", rb_py_file_location]
        )
        assert not result.exit_code, "Failed to compile runbook at {}".format(
            rb_py_file_location
        )
        rb_json = json.loads(result.output)

        # create runbook
        rb_name = "test_decompile_rb_{}".format(uuid.uuid4())

        LOG.info(
            "Creating Runbook at {} with name {}".format(rb_py_file_location, rb_name)
        )
        result = runner.invoke(
            cli, ["-vv", "create", "runbook", "-f", rb_py_file_location, "-n", rb_name]
        )
        assert not result.exit_code, "Failed to create runbook {}".format(rb_name)
        self.created_rb_list.append(rb_name)

        # decompile
        LOG.info("Decompiling runbook {}".format(rb_name))
        result = runner.invoke(cli, ["-vv", "decompile", "runbook", rb_name])
        assert not result.exit_code, "Failed to decompile runbook {}".format(rb_name)
        self.rb_dir_list.append(get_runbook_dir())

        # compile
        decompiled_rb_file_location = os.path.join(get_runbook_dir(), "runbook.py")
        LOG.info(
            "Compiling decompiled runbook file at {}".format(
                decompiled_rb_file_location
            )
        )
        result = runner.invoke(
            cli, ["-vv", "compile", "runbook", "-f", decompiled_rb_file_location]
        )
        assert not result.exit_code, "Failed to compile decompiled runbook {}".format(
            rb_name
        )

        compiled_rb_json = json.loads(result.output)

        # compare
        # names are not preserved for tasks and the runbook itself. So manually address this
        LOG.info("Comparing original and decompiled runbook json")
        compiled_rb_json["metadata"]["name"] = rb_json["metadata"]["name"]
        compiled_rb_json["spec"]["name"] = rb_json["spec"]["name"]
        compiled_rb_json["spec"]["resources"]["default_target_reference"][
            "name"
        ] = rb_json["spec"]["resources"]["default_target_reference"]["name"]
        compiled_rb_json["spec"]["resources"]["endpoint_definition_list"] = rb_json[
            "spec"
        ]["resources"]["endpoint_definition_list"]
        compiled_rb_json["spec"]["resources"]["runbook"]["name"] = rb_json["spec"][
            "resources"
        ]["runbook"]["name"]
        compiled_rb_json["spec"]["resources"]["runbook"]["main_task_local_reference"][
            "name"
        ] = rb_json["spec"]["resources"]["runbook"]["main_task_local_reference"]["name"]
        compiled_rb_json["spec"]["resources"]["runbook"]["task_definition_list"][0][
            "name"
        ] = rb_json["spec"]["resources"]["runbook"]["task_definition_list"][0]["name"]
        compiled_rb_json["spec"]["resources"]["runbook"]["task_definition_list"][1][
            "target_any_local_reference"
        ]["name"] = rb_json["spec"]["resources"]["runbook"]["task_definition_list"][1][
            "target_any_local_reference"
        ][
            "name"
        ]
        assert compiled_rb_json == rb_json
        LOG.info("Success")
