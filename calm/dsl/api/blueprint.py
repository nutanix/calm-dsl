from .resource import ResourceAPI
from .connection import REQUEST
from .util import strip_secrets, patch_secrets
from .project import ProjectAPI


class BlueprintAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="blueprints")
        self.UPLOAD = self.PREFIX + "/import_json"
        self.LAUNCH = self.ITEM + "/simple_launch"
        self.FULL_LAUNCH = self.ITEM + "/launch"
        self.MARKETPLACE_LAUNCH = self.PREFIX + "/marketplace_launch"
        self.LAUNCH_POLL = self.ITEM + "/pending_launches/{}"
        self.BP_EDITABLES = self.ITEM + "/runtime_editables"
        self.EXPORT_JSON = self.ITEM + "/export_json"
        self.EXPORT_JSON_WITH_SECRETS = self.ITEM + "/export_json?keep_secrets=true"
        self.EXPORT_FILE = self.ITEM + "/export_file"
        self.BROWNFIELD_VM_LIST = self.PREFIX + "/brownfield_import/vms/list"

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

    def upload_with_secrets(
        self, bp_name, bp_desc, bp_resources, bp_metadata=None, force_create=False
    ):

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

        secret_map = {}
        secret_variables = []
        object_lists = [
            "service_definition_list",
            "package_definition_list",
            "substrate_definition_list",
            "app_profile_list",
        ]
        strip_secrets(
            bp_resources, secret_map, secret_variables, object_lists=object_lists
        )

        # Handling vmware secrets
        def strip_vmware_secrets(path_list, obj):
            path_list.extend(["create_spec", "resources", "guest_customization"])
            obj = obj["create_spec"]["resources"]["guest_customization"]

            if "windows_data" in obj:
                path_list.append("windows_data")
                obj = obj["windows_data"]

                # Check for admin_password
                if "password" in obj:
                    secret_variables.append(
                        (path_list + ["password"], obj["password"].pop("value", ""))
                    )
                    obj["password"]["attrs"] = {
                        "is_secret_modified": False,
                        "secret_reference": None,
                    }

                # Now check for domain password
                if obj.get("is_domain", False):
                    if "domain_password" in obj:
                        secret_variables.append(
                            (
                                path_list + ["domain_password"],
                                obj["domain_password"].pop("value", ""),
                            )
                        )
                        obj["domain_password"]["attrs"] = {
                            "is_secret_modified": False,
                            "secret_reference": None,
                        }

        for obj_index, obj in enumerate(
            bp_resources.get("substrate_definition_list", []) or []
        ):
            if (obj["type"] == "VMWARE_VM") and (obj["os_type"] == "Windows"):
                strip_vmware_secrets(["substrate_definition_list", obj_index], obj)

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

    def export_json(self, uuid):
        url = self.EXPORT_JSON.format(uuid)
        return self.connection._call(url, verify=False, method=REQUEST.METHOD.GET)

    def export_json_with_secrets(self, uuid):
        url = self.EXPORT_JSON_WITH_SECRETS.format(uuid)
        return self.connection._call(url, verify=False, method=REQUEST.METHOD.GET)

    def export_file(self, uuid):
        return self.connection._call(
            self.EXPORT_FILE.format(uuid), verify=False, method=REQUEST.METHOD.GET
        )
