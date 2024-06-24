
import os
import pytest
import copy
import json

from calm.dsl.cli.utils import insert_uuid

class TestInsertUuid:
    def test_insert_uuid_with_same_action_and_task_names(self):
        json_file = "action_with_same_task_name.json"
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(dir_path + '/utils_payload', json_file)
        action = json.loads(open(file_path).read())

        name_uuid_map = {}
        action_list_with_uuid = copy.deepcopy(action)
        entity_key = ""

        insert_uuid(action, name_uuid_map, action_list_with_uuid, entity_key)

        assert action_list_with_uuid["uuid"] != action_list_with_uuid["runbook"]["task_definition_list"][1]["uuid"]
        assert action_list_with_uuid["runbook"]["task_definition_list"][1]["uuid"] == action_list_with_uuid["runbook"]["task_definition_list"][0]["child_tasks_local_reference_list"][0]["uuid"]

    def test_insert_uuid_with_same_variable_names(self):
        json_file = "action_task_with_same_variable_names.json"
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(dir_path + '/utils_payload', json_file)
        action = json.loads(open(file_path).read())

        name_uuid_map = {}
        action_list_with_uuid = copy.deepcopy(action)
        entity_key = ""

        insert_uuid(action, name_uuid_map, action_list_with_uuid, entity_key)

        assert action_list_with_uuid["runbook"]["variable_list"][0]["uuid"] != action_list_with_uuid["runbook"]["task_definition_list"][1]["variable_list"][0]["uuid"]
        assert action_list_with_uuid["runbook"]["variable_list"][0]["value"] == "action_var1_value"
        assert action_list_with_uuid["runbook"]["task_definition_list"][1]["variable_list"][0]["value"] == "action_var2_value"

    def test_insert_uuid_with_same_header_names(self):
        json_file = "action_task_with_same_header_names.json"
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(dir_path + '/utils_payload', json_file)
        action = json.loads(open(file_path).read())

        name_uuid_map = {}
        action_list_with_uuid = copy.deepcopy(action)
        entity_key = ""

        insert_uuid(action, name_uuid_map, action_list_with_uuid, entity_key)

        assert action_list_with_uuid["runbook"]["variable_list"][0]["options"]["attrs"]["headers"][0]["uuid"] != action_list_with_uuid["runbook"]["variable_list"][1]["options"]["attrs"]["headers"][0]["uuid"]

    def test_insert_uuid_with_same_input_output_variable_names(self):
        json_file = "action_task_with_same_input_output_variable_names.json"
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(dir_path + '/utils_payload', json_file)
        action = json.loads(open(file_path).read())

        name_uuid_map = {}
        action_list_with_uuid = copy.deepcopy(action)
        entity_key = ""

        insert_uuid(action, name_uuid_map, action_list_with_uuid, entity_key)

        assert action_list_with_uuid["runbook"]["variable_list"][0]["uuid"] != action_list_with_uuid["runbook"]["output_variable_list"][0]["uuid"]
        assert action_list_with_uuid["runbook"]["variable_list"][0]["value"] != action_list_with_uuid["runbook"]["output_variable_list"][0]["value"]