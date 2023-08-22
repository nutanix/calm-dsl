import os
import json

from .resource import ResourceAPI
from .connection import REQUEST
from . import util
from .util import (
    strip_secrets,
    patch_secrets,
)
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


class BlueprintAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="blueprints")
        self.UPLOAD = self.PREFIX + "/import_json"
        self.LAUNCH = self.ITEM + "/simple_launch"
        self.FULL_LAUNCH = self.ITEM + "/launch"
        self.MARKETPLACE_LAUNCH = self.PREFIX + "/marketplace_launch"
        self.LAUNCH_POLL = self.ITEM + "/pending_launches/{}"
        self.BP_EDITABLES = self.ITEM + "/runtime_editables"
        self.IMPORT_FILE = self.PREFIX + "/import_file"
        self.EXPORT_JSON = self.ITEM + "/export_json"
        self.EXPORT_JSON_WITH_SECRETS = self.ITEM + "/export_json?keep_secrets=true"
        self.EXPORT_FILE = self.ITEM + "/export_file"
        self.BROWNFIELD_VM_LIST = self.PREFIX + "/brownfield_import/vms/list"
        self.PATCH_WITH_ENVIRONMENT = self.ITEM + "/patch_with_environment"
        self.VARIABLE_VALUES = self.ITEM + "/variables/{}/values"
        self.VARIABLE_VALUES_WITH_TRLID = (
            self.VARIABLE_VALUES + "?requestId={}&trlId={}"
        )
        self.PROTECTION_POLICY_LIST = (
            self.ITEM + "/app_profile/{}/config_spec/{}/app_protection_policies/list"
        )

    # TODO https://jira.nutanix.com/browse/CALM-17178
    # Blueprint creation timeout is dependent on payload.
    # So setting read timeout to 300 seconds
    def upload(self, payload):
        return self.connection._call(
            self.UPLOAD,
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
            timeout=(5, 300),
        )

    def upload_using_import_file(self, payload, files):
        return self.connection._call(
            self.IMPORT_FILE,
            verify=False,
            files=files,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    def launch(self, uuid, payload):
        return self.connection._call(
            self.LAUNCH.format(uuid),
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    def full_launch(self, uuid, payload):
        return self.connection._call(
            self.FULL_LAUNCH.format(uuid),
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    def marketplace_launch(self, payload):
        return self.connection._call(
            self.MARKETPLACE_LAUNCH,
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    def patch_with_environment(self, uuid, payload):
        return self.connection._call(
            self.PATCH_WITH_ENVIRONMENT.format(uuid),
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    def poll_launch(self, blueprint_id, request_id):
        return self.connection._call(
            self.LAUNCH_POLL.format(blueprint_id, request_id),
            verify=False,
            method=REQUEST.METHOD.GET,
        )

    def _get_editables(self, bp_uuid):
        return self.connection._call(
            self.BP_EDITABLES.format(bp_uuid), verify=False, method=REQUEST.METHOD.GET
        )

    def brownfield_vms(self, payload):
        # Adding refresh cache for call. As redis expiry is 10 mins.
        payload["filter"] += ";refresh_cache==True"
        return self.connection._call(
            self.BROWNFIELD_VM_LIST,
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    def protection_policies(
        self, bp_uuid, app_profile_uuid, config_uuid, env_uuid, length=250, offset=0
    ):
        payload = {
            "length": 250,
            "offset": 0,
            "filter": "environment_references=={}".format(env_uuid),
        }
        return self.connection._call(
            self.PROTECTION_POLICY_LIST.format(bp_uuid, app_profile_uuid, config_uuid),
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    @staticmethod
    def _make_blueprint_payload(bp_name, bp_desc, bp_resources, bp_metadata=None):

        if not bp_metadata:
            bp_metadata = {"spec_version": 1, "name": bp_name, "kind": "blueprint"}

        bp_payload = {
            "spec": {
                "name": bp_name,
                "description": bp_desc or "",
                "resources": bp_resources,
            },
            "metadata": bp_metadata,
            "api_version": "3.0",
        }

        return bp_payload

    def check_if_bp_already_exists(self, bp_name, force_create):
        # check if bp with the given name already exists
        params = {"filter": "name=={};state!=DELETED".format(bp_name)}
        res, err = self.list(params=params)
        if err:
            return None, err

        response = res.json()
        entities = response.get("entities", None)
        if entities:
            if len(entities) > 0:
                if not force_create:
                    err_msg = "Blueprint {} already exists. Use --force to first delete existing blueprint before create.".format(
                        bp_name
                    )
                    # ToDo: Add command to edit Blueprints
                    err = {"error": err_msg, "code": -1}
                    return None, err

                # --force option used in create. Delete existing blueprint with same name.
                bp_uuid = entities[0]["metadata"]["uuid"]
                _, err = self.delete(bp_uuid)
                if err:
                    return None, err
        return None, None

    def upload_with_secrets(
        self, bp_name, bp_desc, bp_resources, bp_metadata=None, force_create=False
    ):
        _, err = self.check_if_bp_already_exists(bp_name, force_create)

        if err:
            return None, err

        secret_map = {}
        secret_variables = []
        object_lists = [
            "service_definition_list",
            "package_definition_list",
            "substrate_definition_list",
            "app_profile_list",
            "credential_definition_list",
        ]
        strip_secrets(
            bp_resources, secret_map, secret_variables, object_lists=object_lists
        )

        for obj_index, obj in enumerate(
            bp_resources.get("substrate_definition_list", []) or []
        ):
            if (obj["type"] == "VMWARE_VM") and (obj["os_type"] == "Windows"):
                util.strip_vmware_secrets(
                    ["substrate_definition_list", obj_index], obj, secret_variables
                )

        upload_payload = self._make_blueprint_payload(
            bp_name, bp_desc, bp_resources, bp_metadata
        )

        # TODO strip categories and add at updating time
        bp_categories = upload_payload["metadata"].pop("categories", {})
        res, err = self.upload(upload_payload)

        if err:
            return res, err

        # Add secrets and update bp
        bp = res.json()
        del bp["status"]

        patch_secrets(bp["spec"]["resources"], secret_map, secret_variables)

        # Adding categories at PUT call to blueprint
        bp["metadata"]["categories"] = bp_categories

        # Update blueprint
        update_payload = bp
        uuid = bp["metadata"]["uuid"]

        return self.update(uuid, update_payload)

    def upload_with_decompiled_secrets(
        self,
        bp_payload,
        bp_resources,
        project_uuid,
        bp_name=None,
        passphrase=None,
        force_create=None,
        decompiled_secrets=[],
    ):
        """
        Used to create a blueprint if it contains encrypted secrets from decompilation

        Args:
            bp_payload (dict): payload of the blueprint
            bp_resources (dict): resources of blueprint
            project_uuid (string): UUID of the project
            bp_name (string): name of the blueprint to be created
            passphrase (string): passphrase for creating blueprint with secrets (it should be same as the one provided while decompilation)
            force_create (boolean): to delete bp with same name(if exists) and create a new one
            decompiled_secrets (list): contains all the secrets that were present in the decompiled blueprint
        """

        _, err = self.check_if_bp_already_exists(bp_name, force_create)

        if err:
            return None, err

        secret_map = {}
        secret_variables = []
        not_stripped_secrets = []
        object_lists = [
            "service_definition_list",
            "package_definition_list",
            "substrate_definition_list",
            "app_profile_list",
            "credential_definition_list",
        ]

        strip_secrets(
            bp_resources,
            secret_map,
            secret_variables,
            object_lists=object_lists,
            decompiled_secrets=decompiled_secrets,
            not_stripped_secrets=not_stripped_secrets,
        )

        for obj_index, obj in enumerate(
            bp_resources.get("substrate_definition_list", []) or []
        ):
            if (obj["type"] == "VMWARE_VM") and (obj["os_type"] == "Windows"):
                util.strip_vmware_secrets(
                    ["substrate_definition_list", obj_index],
                    obj,
                    secret_variables,
                    decompiled_secrets,
                    not_stripped_secrets,
                )

        payload = {"name": bp_name, "project_uuid": project_uuid}

        if passphrase:
            payload["passphrase"] = passphrase

        bp_payload["spec"]["resources"] = bp_resources

        files = {"file": ("file", json.dumps(bp_payload))}

        res, err = self.upload_using_import_file(payload, files)

        if err:
            return res, err

        # Add secrets and update bp
        bp = res.json()
        del bp["status"]

        LOG.info("Patching newly created/updated secrets")
        for k in secret_map:
            LOG.debug("[CREATED/MODIFIED] credential -> '{}'".format(k))
        for s in secret_variables:
            LOG.debug("[CREATED/MODIFIED] variable -> '{}' path: {}".format(s[2], s[0]))

        patch_secrets(
            bp["spec"]["resources"], secret_map, secret_variables, not_stripped_secrets
        )

        # Update blueprint
        update_payload = bp
        uuid = bp["metadata"]["uuid"]

        return self.update(uuid, update_payload)

    def export_json(self, uuid):
        url = self.EXPORT_JSON.format(uuid)
        return self.connection._call(url, verify=False, method=REQUEST.METHOD.GET)

    def export_json_with_secrets(self, uuid):
        url = self.EXPORT_JSON_WITH_SECRETS.format(uuid)
        return self.connection._call(url, verify=False, method=REQUEST.METHOD.GET)

    def export_file(self, uuid, passphrase=None):
        if passphrase:
            return self.connection._call(
                self.EXPORT_FILE.format(uuid),
                verify=False,
                method=REQUEST.METHOD.POST,
                request_json={"passphrase": passphrase},
                files=[],
            )
        return self.connection._call(
            self.EXPORT_FILE.format(uuid), verify=False, method=REQUEST.METHOD.GET
        )

    def variable_values(self, uuid, var_uuid):
        url = self.VARIABLE_VALUES.format(uuid, var_uuid)
        return self.connection._call(
            url, verify=False, method=REQUEST.METHOD.GET, ignore_error=True
        )

    def variable_values_from_trlid(self, uuid, var_uuid, req_id, trl_id):
        url = self.VARIABLE_VALUES_WITH_TRLID.format(uuid, var_uuid, req_id, trl_id)
        return self.connection._call(
            url, verify=False, method=REQUEST.METHOD.GET, ignore_error=True
        )
