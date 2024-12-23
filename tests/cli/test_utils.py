import os
import pytest
import copy
import inspect
import json

from calm.dsl.cli.utils import insert_uuid


class DelayedAssert:
    def __init__(self):
        self._failed_expectations = []

    def expect(self, expr, msg=None):
        """
        Keeps track of failed expectations
        Args:
            expr(bool) : keep track of failures
            msg(str) : assert message
        """

        if not expr:
            self._log_failure(msg)

    def assert_expectations(self):
        """
        raise an assert if there are any failed expectations

        Interface is 2 functions:

          expect(expr, msg=None)
          : Evaluate 'expr' as a boolean, and keeps track of failures

          assert_expectations()
          : raises an assert if an expect() calls failed

        Usage Example:

            from expectations import expect, assert_expectations

            def test_should_pass():
                expect(1 == 1, 'one is one')
                assert_expectations()

            def test_should_fail():
                expect(1 == 2, 'one is two')
                expect(1 == 3, 'one is three')
                assert_expectations()

        """
        if self._failed_expectations:
            assert False, self._report_failures()

    def _log_failure(self, msg=None):
        """
        This routine will log failure
        Args:
            msg(str) : assert message
        """
        (filename, line, funcname, contextlist) = inspect.stack()[2][1:5]
        filename = os.path.basename(filename)
        context = contextlist[0]
        self._failed_expectations.append(
            'file "%s", line %s, in %s()%s\n%s'
            % (filename, line, funcname, (("\n%s" % msg) if msg else ""), context)
        )

    def _report_failures(self):
        """
        This routine will report the various failures which are logged
        Returns:
            str : assert message
        """
        if self._failed_expectations:
            (filename, line, funcname) = inspect.stack()[2][1:4]
            report = [
                "\n\nassert_expectations() called from",
                '"%s" line %s, in %s()\n'
                % (os.path.basename(filename), line, funcname),
                "Failed Expectations:%s\n" % len(self._failed_expectations),
            ]
            for i, failure in enumerate(self._failed_expectations, start=1):
                report.append("%d: %s" % (i, failure))
            _failed_expectations = []
        return "\n".join(report)


class TestInsertUuid:
    def test_insert_uuid_with_same_action_and_task_names(self):
        json_file = "action_with_same_task_name.json"
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(dir_path + "/utils_payload", json_file)
        action = json.loads(open(file_path).read())

        name_uuid_map = {}
        action_list_with_uuid = copy.deepcopy(action)
        entity_key = ""

        insert_uuid(action, name_uuid_map, action_list_with_uuid, entity_key)

        assert (
            action_list_with_uuid["uuid"]
            != action_list_with_uuid["runbook"]["task_definition_list"][1]["uuid"]
        )
        assert (
            action_list_with_uuid["runbook"]["task_definition_list"][1]["uuid"]
            == action_list_with_uuid["runbook"]["task_definition_list"][0][
                "child_tasks_local_reference_list"
            ][0]["uuid"]
        )

    def test_insert_uuid_with_same_variable_names(self):
        json_file = "action_task_with_same_variable_names.json"
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(dir_path + "/utils_payload", json_file)
        action = json.loads(open(file_path).read())

        name_uuid_map = {}
        action_list_with_uuid = copy.deepcopy(action)
        entity_key = ""

        insert_uuid(action, name_uuid_map, action_list_with_uuid, entity_key)

        assert (
            action_list_with_uuid["runbook"]["variable_list"][0]["uuid"]
            != action_list_with_uuid["runbook"]["task_definition_list"][1][
                "variable_list"
            ][0]["uuid"]
        )
        assert (
            action_list_with_uuid["runbook"]["variable_list"][0]["value"]
            == "action_var1_value"
        )
        assert (
            action_list_with_uuid["runbook"]["task_definition_list"][1][
                "variable_list"
            ][0]["value"]
            == "action_var2_value"
        )

    def test_insert_uuid_with_same_header_names(self):
        json_file = "action_task_with_same_header_names.json"
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(dir_path + "/utils_payload", json_file)
        action = json.loads(open(file_path).read())

        name_uuid_map = {}
        action_list_with_uuid = copy.deepcopy(action)
        entity_key = ""

        insert_uuid(action, name_uuid_map, action_list_with_uuid, entity_key)

        assert (
            action_list_with_uuid["runbook"]["variable_list"][0]["options"]["attrs"][
                "headers"
            ][0]["uuid"]
            != action_list_with_uuid["runbook"]["variable_list"][1]["options"]["attrs"][
                "headers"
            ][0]["uuid"]
        )

    def test_insert_uuid_with_same_input_output_variable_names(self):
        json_file = "action_task_with_same_input_output_variable_names.json"
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(dir_path + "/utils_payload", json_file)
        action = json.loads(open(file_path).read())

        name_uuid_map = {}
        action_list_with_uuid = copy.deepcopy(action)
        entity_key = ""

        insert_uuid(action, name_uuid_map, action_list_with_uuid, entity_key)

        assert (
            action_list_with_uuid["runbook"]["variable_list"][0]["uuid"]
            != action_list_with_uuid["runbook"]["output_variable_list"][0]["uuid"]
        )
        assert (
            action_list_with_uuid["runbook"]["variable_list"][0]["value"]
            != action_list_with_uuid["runbook"]["output_variable_list"][0]["value"]
        )

    def test_insert_uuid_with_action_having_multiple_tasks(self):
        json_file = "action_task_with_multiple_tasks.json"
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(dir_path + "/utils_payload", json_file)
        action = json.loads(open(file_path).read())

        name_uuid_map = {}
        action_list_with_uuid = copy.deepcopy(action)
        entity_key = ""

        insert_uuid(action, name_uuid_map, action_list_with_uuid, entity_key)

        assert (
            "uuid"
            in action_list_with_uuid["runbook"]["task_definition_list"][0]["attrs"][
                "edges"
            ][0]
        ), "UUID is missing in edges"
