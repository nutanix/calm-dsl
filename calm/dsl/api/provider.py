import json
import os

from calm.dsl.log import get_logging_handle

from .resource import ResourceAPI
from .connection import REQUEST
from .util import strip_provider_secrets, patch_secrets, strip_uuids

LOG = get_logging_handle(__name__)


class ProviderAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="providers", calm_api=True)

        self.CREATE = self.PREFIX
        self.BULK_CREATE = self.CREATE + "/bulk"
        self.BULK_UPDATE = self.ITEM + "/bulk"
        self.BULK_READ = self.ITEM + "/bulk"
        self.COMPILE = self.ITEM + "/compile"
        self.TEST_PROVIDER_VERIFY = self.PREFIX + "/{}/actions/{}/test_run"
        self.ABORT_RUN = self.ITEM + "/runlogs/{}/abort"
        self.POLL_RUN = self.ITEM + "/runlogs/{}"
        self.CHILD_RUNLOG_LIST = self.ITEM + "/runlogs/{}/children/list"
        self.RUNLOG_OUTPUT = self.ITEM + "/runlogs/{}/children/{}/output"
        self.RUNLOG_LIST = self.CREATE + "/runlogs/list"
        self.CLONE = self.ITEM + "/clone"
        self.IMPORT_JSON = self.PREFIX + "/import_json"
        self.IMPORT_FILE = self.PREFIX + "/import_file"
        self.EXPORT_JSON = self.ITEM + "/export_json"
        self.EXPORT_FILE = self.ITEM + "/export_file"

    def check_if_provider_already_exists(self, provider_name):
        params = {"filter": "name=={};state!=DELETED".format(provider_name)}
        res, err = self.list(params=params)
        if err:
            return None, err

        response = res.json()
        entities = response.get("entities", None)
        if entities and len(entities) > 0:
            return entities[0], None
        return None, None

    def create(self, provider_payload):
        return self.connection._call(
            self.CREATE,
            verify=False,
            request_json=provider_payload,
            method=REQUEST.METHOD.POST,
            timeout=(5, 300),
        )

    # This is equivalent to "compile" of whole Provider tree as present in Calm UI
    def preview_validate(self, uuid):
        return self.connection._call(
            self.COMPILE.format(uuid), verify=False, method=REQUEST.METHOD.GET
        )

    def bulk_create(self, provider_payload):
        res, err = self.connection._call(
            self.BULK_CREATE,
            verify=False,
            request_json=provider_payload,
            method=REQUEST.METHOD.POST,
        )
        if err:
            return res, err

        return self.preview_validate(res.json()["metadata"]["uuid"])

    def bulk_read(self, id):
        return self.connection._call(
            self.BULK_READ.format(id), verify=False, method=REQUEST.METHOD.GET
        )

    def bulk_update(self, uuid, provider_payload):
        res, err = self.connection._call(
            self.BULK_UPDATE.format(uuid),
            verify=False,
            request_json=provider_payload,
            method=REQUEST.METHOD.PUT,
        )
        if err:
            return res, err

        return self.preview_validate(uuid)

    def run(self, uuid, action_uuid, payload):
        return self.connection._call(
            self.TEST_PROVIDER_VERIFY.format(uuid, action_uuid),
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    def list_child_runlogs(self, provider_uuid, runlog_uuid):
        return self.connection._call(
            self.CHILD_RUNLOG_LIST.format(provider_uuid, runlog_uuid),
            verify=False,
            request_json={},
            method=REQUEST.METHOD.POST,
        )

    def list_runlogs(self, payload=None):
        return self.connection._call(
            self.RUNLOG_LIST,
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    def runlog_output(self, provider_uuid, runlog_uuid, child_runlog_uuid):
        return self.connection._call(
            self.RUNLOG_OUTPUT.format(provider_uuid, runlog_uuid, child_runlog_uuid),
            verify=False,
            method=REQUEST.METHOD.GET,
        )

    def poll_action_run(self, uuid, runlog_uuid, payload=None):
        if payload:
            return self.connection._call(
                self.POLL_RUN.format(uuid, runlog_uuid),
                request_json=payload,
                verify=False,
                method=REQUEST.METHOD.POST,
            )
        else:
            return self.connection._call(
                self.POLL_RUN.format(uuid, runlog_uuid),
                verify=False,
                method=REQUEST.METHOD.GET,
            )

    def abort(self, uuid, runlog_uuid):
        return self.connection._call(
            self.ABORT_RUN.format(uuid, runlog_uuid),
            verify=False,
            request_json={},
            method=REQUEST.METHOD.POST,
        )

    def clone(self, uuid, clone_payload):
        return self.connection._call(
            self.CLONE.format(uuid),
            verify=False,
            request_json=clone_payload,
            method=REQUEST.METHOD.POST,
        )

    def import_json(self, provider_json):
        return self.connection._call(
            self.IMPORT_JSON,
            verify=False,
            request_json=provider_json,
            method=REQUEST.METHOD.POST,
        )

    def export_json(self, uuid):
        return self.connection._call(
            self.EXPORT_JSON.format(uuid), verify=False, method=REQUEST.METHOD.GET
        )

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

    def export_provider(self, uuid, passphrase=None):
        current_path = os.path.dirname(os.path.realpath(__file__))
        if passphrase:
            res, err = self.connection._call(
                self.EXPORT_FILE.format(uuid),
                verify=False,
                method=REQUEST.METHOD.POST,
                request_json={"passphrase": passphrase},
                files=[],
            )
        else:
            res, err = self.connection._call(
                self.EXPORT_FILE.format(uuid), verify=False, method=REQUEST.METHOD.GET
            )

        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        with open(current_path + "/" + uuid + ".json", "wb") as downloaded_file:
            for chunk in res.iter_content(chunk_size=2048):
                downloaded_file.write(chunk)

        return current_path + "/" + uuid + ".json"

    def upload_using_import_file(self, payload, files):
        return self.connection._call(
            self.IMPORT_FILE,
            verify=False,
            files=files,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    def upload_with_decompiled_secrets(
        self,
        provider_payload,
        passphrase,
        decompiled_secrets=[],
    ):
        """
        Used to create a provider if it contains encrypted secrets from decompilation

        Args:
            provider_payload (dict): payload of the provider
            passphrase (string): passphrase for creating provider with secrets (it should be same as the one provided while decompilation)
            decompiled_secrets (list): contains all the secrets that were present in the decompiled provider
        """
        secret_map = {}
        secret_variables = []
        not_stripped_secrets = []
        provider_name = provider_payload["spec"]["name"]
        provider_resources = provider_payload["spec"]["resources"]
        LOG.debug("provider_resources pre-stripping secrets")
        LOG.debug(provider_resources)
        strip_provider_secrets(
            provider_name,
            provider_resources,
            secret_map,
            secret_variables,
            decompiled_secrets=decompiled_secrets,
            not_stripped_secrets=not_stripped_secrets,
        )
        LOG.debug("provider_resources post-stripping secrets")
        LOG.debug(provider_resources)

        strip_uuids(provider_resources)
        LOG.debug("provider_resources post-stripping UUIDs")
        LOG.debug(provider_resources)
        provider_payload["spec"]["resources"] = provider_resources
        files = {"file": ("file", json.dumps(provider_payload))}
        res, err = self.upload_using_import_file(
            {"name": provider_name, "passphrase": passphrase}, files
        )
        if err:
            return res, err

        # Add secrets and update provider
        provider = res.json()
        del provider["status"]
        LOG.info("Patching newly created/updated secrets")
        for k in secret_map:
            LOG.debug("[CREATED/MODIFIED] credential -> '{}'".format(k))
        for s in secret_variables:
            LOG.debug("[CREATED/MODIFIED] variable -> '{}' path: {}".format(s[2], s[0]))

        patch_secrets(
            provider["spec"]["resources"],
            secret_map,
            secret_variables,
            not_stripped_secrets,
        )
        LOG.debug("Update provider payload:")
        LOG.debug(provider)

        # Update provider
        update_payload = provider
        uuid = provider["metadata"]["uuid"]
        return self.bulk_update(uuid, update_payload)
