import pytest
import uuid

from calm.dsl.cli.main import get_api_client
from calm.dsl.cli.constants import RUNLOG, MARKETPLACE_ITEM
from runbook_definition import DslRunbookForMPI
from tests.api_interface.test_runbooks.utils import (upload_runbook, poll_runlog_status, read_test_config, change_uuids)
from utils import (publish_runbook_to_marketplace_manager, change_state,
                   clone_marketplace_runbook, execute_marketplace_runbook,
                   get_project_id_from_name)

LinuxEndpointPayload = read_test_config(file_name="linux_endpoint_payload.json")
WindowsEndpointPayload = read_test_config(file_name="windows_endpoint_payload.json")
HTTPEndpointPayload = read_test_config(file_name="http_endpoint_payload.json")


class TestMarketplaceRunbook:

    @classmethod
    def setup_class(cls):
        '''setting up'''

        client = get_api_client()
        cls.runbook_name = "test_publish_runbook_" + str(uuid.uuid4())[-10:]
        rb = upload_runbook(client, cls.runbook_name, DslRunbookForMPI)
        rb_state = rb["status"]["state"]
        rb_uuid = rb["metadata"]["uuid"]
        print(">> Runbook state: {}".format(rb_state))
        cls.runbook_uuid = rb_uuid

        cls.default_project_endpoints = {}
        endpoint_uuids = []
        default_endpoint_uuid = rb['status']['resources'].get("default_target_reference", {}).get("uuid", "")
        if default_endpoint_uuid:
            res, err = client.endpoint.read(default_endpoint_uuid)
            ep = res.json()
            ep_type = ep['spec']['resources']['type']
            ep_name = ep["spec"]["name"]
            cls.default_project_endpoints[ep_type] = (ep_name, default_endpoint_uuid)
            endpoint_uuids.append(default_endpoint_uuid)
            cls.default_endpoint_details = {
                "uuid": default_endpoint_uuid,
                "type": ep_type,
                "name": ep_name
            }

        for task in rb['status']['resources']['runbook']['task_definition_list']:
            ep_uuid = task.get('target_any_local_reference', {}).get('uuid', '')
            if ep_uuid and ep_uuid not in endpoint_uuids:
                res, err = client.endpoint.read(ep_uuid)
                ep = res.json()
                ep_type = ep['spec']['resources']['type']
                ep_name = ep["spec"]["name"]
                cls.default_project_endpoints[ep_type] = (ep_name, ep_uuid)
                endpoint_uuids.append(ep_uuid)

        cls.second_project_name = "rbac_bp_test_project"
        cls.second_project_uuid = get_project_id_from_name(client, cls.second_project_name)
        if cls.second_project_uuid:
            cls.second_project_endpoints = {}
            for endpoint_payload in [LinuxEndpointPayload, WindowsEndpointPayload, HTTPEndpointPayload]:
                endpoint = change_uuids(endpoint_payload, {})
                endpoint['metadata']['project_reference'] = {
                    "kind": "project",
                    "uuid": cls.second_project_uuid,
                    "name": cls.second_project_name
                }
                endpoint['spec']['name'] = "Endpoint_{}_{}".format(cls.second_project_name,
                                                                   str(uuid.uuid4())[-10:])
                # Endpoint Create
                res, err = client.endpoint.create(endpoint)
                ep = res.json()
                ep_state = ep["status"]["state"]
                ep_uuid = ep["metadata"]["uuid"]
                ep_name = ep["spec"]["name"]
                ep_type = ep['spec']['resources']['type']
                print(">> Endpoint created with name {} is in state: {}".format(ep_name, ep_state))
                cls.second_project_endpoints[ep_type] = (ep_name, ep_uuid)

    @pytest.mark.mpi
    @pytest.mark.regression
    @pytest.mark.parametrize("with_secrets", [True, False])
    @pytest.mark.parametrize("with_endpoints", [True, False])
    def test_publish_runbook(self, with_secrets, with_endpoints):
        """
        test_runbook_publish_with_secret_with_endpoint_with_version
        test_runbook_publish_without_secret_with_endpoint
        test_runbook_publish_without_secret_without_endpoint
        test_runbook_publish_with_secret_without_endpoint
        """
        client = get_api_client()

        res, err = client.runbook.read(self.runbook_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        rb = res.json()

        rb_state = rb["status"]["state"]
        print(">> Runbook state: {}".format(rb_state))
        assert rb_state == "ACTIVE"
        assert self.runbook_name == rb["spec"]["name"]
        assert self.runbook_name == rb["metadata"]["name"]

        mpi_name = "test_publish_mpi_" + str(uuid.uuid4())[-10:]
        version = '1.0.0'
        print(">> Publishing mpi {} - {}, with_secrets {} and with endpoints {}".format(
            mpi_name, version, with_secrets, with_endpoints))

        mpi = publish_runbook_to_marketplace_manager(
            client,
            self.runbook_uuid,
            mpi_name,
            version,
            with_secrets=with_secrets,
            with_endpoints=with_endpoints
        )
        mpi_state = mpi["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == "PENDING"
        assert mpi_name == mpi["spec"]["name"]
        assert mpi_name == mpi["metadata"]["name"]

        runbook_template_info = mpi['status']['resources']['runbook_template_info']
        assert self.runbook_uuid == runbook_template_info['source_runbook_reference']['uuid']
        assert with_secrets == runbook_template_info.get('is_published_with_secrets', None)
        assert with_endpoints == runbook_template_info.get('is_published_with_endpoints', None)

    @pytest.mark.mpi
    @pytest.mark.regression
    @pytest.mark.parametrize("state", [MARKETPLACE_ITEM.STATES.ACCEPTED, MARKETPLACE_ITEM.STATES.REJECTED])
    def test_approve_and_reject_runbook_marketplace(self, state):
        """
        test_marketplace_runbook_approve_market_manager
        test_reject_runbook
        """
        client = get_api_client()

        res, err = client.runbook.read(self.runbook_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        rb = res.json()

        rb_state = rb["status"]["state"]
        print(">> Runbook {} state: {}".format(self.runbook_uuid, rb_state))
        assert rb_state == "ACTIVE"
        assert self.runbook_name == rb["spec"]["name"]
        assert self.runbook_name == rb["metadata"]["name"]

        mpi_name = "test_publish_mpi_" + str(uuid.uuid4())[-10:]
        version = '1.0.0'
        print(">> Publishing mpi {} - {}".format(
            mpi_name, version))

        mpi_data = publish_runbook_to_marketplace_manager(
            client,
            self.runbook_uuid,
            mpi_name,
            version,
        )
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.PENDING
        assert mpi_name == mpi_data["spec"]["name"]
        assert mpi_name == mpi_data["metadata"]["name"]

        runbook_template_info = mpi_data['status']['resources']['runbook_template_info']
        assert self.runbook_uuid == runbook_template_info['source_runbook_reference']['uuid']

        mpi_uuid = mpi_data['metadata']['uuid']
        mpi_data = change_state(client, mpi_uuid, state)
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == state

    @pytest.mark.mpi
    @pytest.mark.regression
    def test_mpi_different_version(self):
        """ test_same_runbook_publish_with_secret_with_endpoint_with_different_version """
        client = get_api_client()

        res, err = client.runbook.read(self.runbook_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        rb = res.json()

        rb_state = rb["status"]["state"]
        print(">> Runbook {} state: {}".format(self.runbook_uuid, rb_state))
        assert rb_state == "ACTIVE"
        assert self.runbook_name == rb["spec"]["name"]
        assert self.runbook_name == rb["metadata"]["name"]

        mpi_name = "test_publish_mpi_" + str(uuid.uuid4())[-10:]
        version = '1.0.0'
        print(">> Publishing mpi {} - {}".format(
            mpi_name, version))

        mpi_data = publish_runbook_to_marketplace_manager(
            client,
            self.runbook_uuid,
            mpi_name,
            version,
        )
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.PENDING
        assert mpi_name == mpi_data["spec"]["name"]
        assert mpi_name == mpi_data["metadata"]["name"]
        assert version == mpi_data["status"]["resources"]["version"]

        app_group_uuid = mpi_data["status"]["resources"]["app_group_uuid"]
        new_mpi_version = "2.0.0"
        with_secrets = True
        with_endpoints = True
        print(">> Publishing mpi {} - {}, with_secrets {} and with endpoints {}".format(
            mpi_name, new_mpi_version, with_secrets, with_endpoints))

        new_mpi_data = publish_runbook_to_marketplace_manager(
            client,
            self.runbook_uuid,
            mpi_name,
            new_mpi_version,
            with_secrets=with_secrets,
            with_endpoints=with_endpoints,
            app_group_uuid=app_group_uuid
        )

        new_mpi_state = new_mpi_data["status"]["resources"]["app_state"]
        print(">> New MPI state: {}".format(new_mpi_state))
        assert new_mpi_state == MARKETPLACE_ITEM.STATES.PENDING
        assert mpi_name == new_mpi_data["spec"]["name"]
        assert mpi_name == new_mpi_data["metadata"]["name"]
        assert new_mpi_version == new_mpi_data["status"]["resources"]["version"]

        new_app_group_uuid = new_mpi_data["status"]["resources"]["app_group_uuid"]
        assert app_group_uuid == new_app_group_uuid

        runbook_template_info = new_mpi_data['status']['resources']['runbook_template_info']
        assert with_secrets == runbook_template_info.get('is_published_with_secrets', None)
        assert with_endpoints == runbook_template_info.get('is_published_with_endpoints', None)

    @pytest.mark.mpi
    @pytest.mark.regression
    def test_publish_runbook_store(self):
        """ test_marketplace_runbook_publish_market_manager """
        client = get_api_client()

        res, err = client.runbook.read(self.runbook_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        rb = res.json()

        rb_state = rb["status"]["state"]
        print(">> Runbook {} state: {}".format(self.runbook_uuid, rb_state))
        assert rb_state == "ACTIVE"
        assert self.runbook_name == rb["spec"]["name"]
        assert self.runbook_name == rb["metadata"]["name"]

        mpi_name = "test_publish_mpi_" + str(uuid.uuid4())[-10:]
        version = '1.0.0'
        print(">> Publishing mpi {} - {}".format(
            mpi_name, version))

        mpi_data = publish_runbook_to_marketplace_manager(
            client,
            self.runbook_uuid,
            mpi_name,
            version,
        )
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.PENDING
        assert mpi_name == mpi_data["spec"]["name"]
        assert mpi_name == mpi_data["metadata"]["name"]

        runbook_template_info = mpi_data['status']['resources']['runbook_template_info']
        assert self.runbook_uuid == runbook_template_info['source_runbook_reference']['uuid']

        mpi_uuid = mpi_data['metadata']['uuid']
        mpi_data = change_state(client, mpi_uuid, MARKETPLACE_ITEM.STATES.ACCEPTED)
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.ACCEPTED

        mpi_data = change_state(client, mpi_uuid, MARKETPLACE_ITEM.STATES.PUBLISHED)
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.PUBLISHED

    @pytest.mark.mpi
    @pytest.mark.regression
    @pytest.mark.parametrize("with_endpoints", [True, False])
    def test_mpi_runbook_clone_same_project(self, with_endpoints):
        """
        test_mpi_runbook_with_endpoint_clone_same_project
        test_mpi_runbook_without_endpoint_clone_same_project
        """
        client = get_api_client()
        res, err = client.runbook.read(self.runbook_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        rb = res.json()

        rb_state = rb["status"]["state"]
        print(">> Runbook {} state: {}".format(self.runbook_uuid, rb_state))
        assert rb_state == "ACTIVE"
        assert self.runbook_name == rb["spec"]["name"]
        assert self.runbook_name == rb["metadata"]["name"]

        mpi_name = "test_clone_mpi_" + str(uuid.uuid4())[-10:]
        version = '1.0.0'
        print(">> Publishing mpi {} - {}".format(
            mpi_name, version))

        mpi_data = publish_runbook_to_marketplace_manager(
            client,
            self.runbook_uuid,
            mpi_name,
            version,
            with_endpoints=with_endpoints,
            with_secrets=True
        )
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.PENDING
        assert mpi_name == mpi_data["spec"]["name"]
        assert mpi_name == mpi_data["metadata"]["name"]

        runbook_template_info = mpi_data['status']['resources']['runbook_template_info']
        assert self.runbook_uuid == runbook_template_info['source_runbook_reference']['uuid']

        mpi_uuid = mpi_data['metadata']['uuid']
        mpi_data = change_state(client, mpi_uuid, MARKETPLACE_ITEM.STATES.ACCEPTED)
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.ACCEPTED

        mpi_data = change_state(client, mpi_uuid, MARKETPLACE_ITEM.STATES.PUBLISHED, project_list=['default'])
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.PUBLISHED

        cloned_rb_name = self.runbook_name + "_cloned_" + str(uuid.uuid4())[-10:]
        cloned_runbook_uuid = clone_marketplace_runbook(client, mpi_uuid,
                                                        cloned_rb_name,
                                                        project_name="default")

        res, err = client.runbook.read(cloned_runbook_uuid)

        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        cloned_rb = res.json()
        cloned_rb_state = cloned_rb["status"]["state"]

        assert cloned_rb_name == cloned_rb["spec"]["name"]
        assert cloned_rb_name == cloned_rb["metadata"]["name"]

        print(">> Runbook state: {}".format(cloned_rb_state))
        if with_endpoints:
            assert cloned_rb_state == "ACTIVE", "Runbook published with endpoints should be in Active state"
        else:
            assert cloned_rb_state == "DRAFT", "Runbook published without endpoints should be in Draft state"

    @pytest.mark.mpi
    @pytest.mark.regression
    @pytest.mark.parametrize("with_endpoints", [True, False])
    def test_mpi_runbook_clone_different_project(self, with_endpoints):
        """
        test_mpi_runbook_with_endpoint_clone_same_project
        test_mpi_runbook_without_endpoint_clone_same_project
        """
        client = get_api_client()
        res, err = client.runbook.read(self.runbook_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        rb = res.json()

        rb_state = rb["status"]["state"]
        print(">> Runbook {} state: {}".format(self.runbook_uuid, rb_state))
        assert rb_state == "ACTIVE"
        assert self.runbook_name == rb["spec"]["name"]
        assert self.runbook_name == rb["metadata"]["name"]

        mpi_name = "test_clone_mpi_" + str(uuid.uuid4())[-10:]
        version = '1.0.0'
        print(">> Publishing mpi {} - {}".format(
            mpi_name, version))

        mpi_data = publish_runbook_to_marketplace_manager(
            client,
            self.runbook_uuid,
            mpi_name,
            version,
            with_endpoints=with_endpoints,
            with_secrets=True
        )
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.PENDING
        assert mpi_name == mpi_data["spec"]["name"]
        assert mpi_name == mpi_data["metadata"]["name"]

        runbook_template_info = mpi_data['status']['resources']['runbook_template_info']
        assert self.runbook_uuid == runbook_template_info['source_runbook_reference']['uuid']

        mpi_uuid = mpi_data['metadata']['uuid']
        mpi_data = change_state(client, mpi_uuid, MARKETPLACE_ITEM.STATES.ACCEPTED)
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.ACCEPTED

        mpi_data = change_state(client, mpi_uuid, MARKETPLACE_ITEM.STATES.PUBLISHED, project_list=['default'])
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.PUBLISHED

        cloned_rb_name = self.runbook_name + "_cloned_" + str(uuid.uuid4())[-10:]
        cloned_runbook_uuid = clone_marketplace_runbook(client, mpi_uuid,
                                                        cloned_rb_name,
                                                        project_name=self.second_project_name)

        res, err = client.runbook.read(cloned_runbook_uuid)

        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        cloned_rb = res.json()
        cloned_rb_state = cloned_rb["status"]["state"]

        assert cloned_rb_name == cloned_rb["spec"]["name"]
        assert cloned_rb_name == cloned_rb["metadata"]["name"]

        print(">> Runbook state: {}".format(cloned_rb_state))
        assert cloned_rb_state == "DRAFT", "Runbook published without endpoints should be in Draft state"

    @pytest.mark.mpi
    @pytest.mark.regression
    @pytest.mark.parametrize("with_endpoints", [True, False])
    def test_mpi_runbook_execute_same_project(self, with_endpoints):
        """
        test_mpi_runbook_with_endpoint_clone_same_project
        test_mpi_runbook_without_endpoint_clone_same_project
        """
        client = get_api_client()
        res, err = client.runbook.read(self.runbook_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        rb = res.json()

        rb_state = rb["status"]["state"]
        print(">> Runbook {} state: {}".format(self.runbook_uuid, rb_state))
        assert rb_state == "ACTIVE"
        assert self.runbook_name == rb["spec"]["name"]
        assert self.runbook_name == rb["metadata"]["name"]

        mpi_name = "test_execute_mpi_" + str(uuid.uuid4())[-10:]
        version = '1.0.0'
        print(">> Publishing mpi {} - {}".format(
            mpi_name, version))

        mpi_data = publish_runbook_to_marketplace_manager(
            client,
            self.runbook_uuid,
            mpi_name,
            version,
            with_endpoints=with_endpoints,
            with_secrets=True
        )
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.PENDING
        assert mpi_name == mpi_data["spec"]["name"]
        assert mpi_name == mpi_data["metadata"]["name"]

        runbook_template_info = mpi_data['status']['resources']['runbook_template_info']
        assert self.runbook_uuid == runbook_template_info['source_runbook_reference']['uuid']

        mpi_uuid = mpi_data['metadata']['uuid']
        mpi_data = change_state(client, mpi_uuid, MARKETPLACE_ITEM.STATES.ACCEPTED)
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.ACCEPTED

        mpi_data = change_state(client, mpi_uuid, MARKETPLACE_ITEM.STATES.PUBLISHED, project_list=['default'])
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.PUBLISHED

        endpoints_mapping = {}
        default_endpoint_uuid = None
        if not with_endpoints:
            for ep_name, ep_uuid in self.default_project_endpoints.values():
                endpoints_mapping[ep_name] = ep_uuid
            default_endpoint_uuid = self.default_endpoint_details.get("uuid", None)

        runlog_uuid = execute_marketplace_runbook(client, mpi_uuid,
                                                  default_endpoint_uuid=default_endpoint_uuid,
                                                  endpoints_mapping=endpoints_mapping,
                                                  project_name="default")

        # polling till runbook run gets to terminal state
        state, reasons = poll_runlog_status(
            client, runlog_uuid, RUNLOG.TERMINAL_STATES, maxWait=360
        )

        print(">> Runbook Run state: {}\n{}".format(state, reasons))
        assert state == RUNLOG.STATUS.SUCCESS

    @pytest.mark.mpi
    @pytest.mark.regression
    @pytest.mark.parametrize("with_endpoints", [True, False])
    def test_mpi_runbook_execute_different_project(self, with_endpoints):
        """
        test_mpi_runbook_with_endpoint_clone_same_project
        test_mpi_runbook_without_endpoint_clone_same_project
        """
        client = get_api_client()
        res, err = client.runbook.read(self.runbook_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        rb = res.json()

        rb_state = rb["status"]["state"]
        print(">> Runbook {} state: {}".format(self.runbook_uuid, rb_state))
        assert rb_state == "ACTIVE"
        assert self.runbook_name == rb["spec"]["name"]
        assert self.runbook_name == rb["metadata"]["name"]

        mpi_name = "test_execute_mpi_" + str(uuid.uuid4())[-10:]
        version = '1.0.0'
        print(">> Publishing mpi {} - {}".format(
            mpi_name, version))

        mpi_data = publish_runbook_to_marketplace_manager(
            client,
            self.runbook_uuid,
            mpi_name,
            version,
            with_endpoints=with_endpoints,
            with_secrets=True
        )
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.PENDING
        assert mpi_name == mpi_data["spec"]["name"]
        assert mpi_name == mpi_data["metadata"]["name"]

        runbook_template_info = mpi_data['status']['resources']['runbook_template_info']
        assert self.runbook_uuid == runbook_template_info['source_runbook_reference']['uuid']

        mpi_uuid = mpi_data['metadata']['uuid']
        mpi_data = change_state(client, mpi_uuid, MARKETPLACE_ITEM.STATES.ACCEPTED)
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.ACCEPTED

        mpi_data = change_state(client, mpi_uuid, MARKETPLACE_ITEM.STATES.PUBLISHED, project_list=['default'])
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.PUBLISHED

        endpoints_mapping = {}
        default_endpoint_uuid = None
        if not with_endpoints:
            print(self.default_project_endpoints, self.second_project_endpoints)
            for ep_type, ep_info in self.default_project_endpoints.items():
                second_project_ep_info = self.second_project_endpoints.get(ep_type)
                endpoints_mapping[ep_info[0]] = second_project_ep_info[1]

            default_endpoint_type = self.default_endpoint_details.get("type")
            default_endpoint_uuid = self.second_project_endpoints[default_endpoint_type][1]

        runlog_uuid = execute_marketplace_runbook(client, mpi_uuid,
                                                  default_endpoint_uuid=default_endpoint_uuid,
                                                  endpoints_mapping=endpoints_mapping,
                                                  project_name=self.second_project_name)

        # polling till runbook run gets to terminal state
        state, reasons = poll_runlog_status(
            client, runlog_uuid, RUNLOG.TERMINAL_STATES, maxWait=360
        )

        print(">> Runbook Run state: {}\n{}".format(state, reasons))
        assert state == RUNLOG.STATUS.SUCCESS
