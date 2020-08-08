import pytest
import uuid

from calm.dsl.cli.main import get_api_client
from calm.dsl.cli.constants import RUNLOG, MARKETPLACE_ITEM
from tests.sample_runbooks import DslRunbookWithVariables
from tests.api_interface.test_runbooks.utils import upload_runbook, poll_runlog_status, read_test_config
from utils import publish_runbook_to_marketplace_manager, change_state


class TestMarketplaceRunbook:
    publish_runbook_uuid = None

    @pytest.mark.mpi
    @pytest.mark.regression
    @pytest.mark.parametrize("with_secrets", [True, False])
    @pytest.mark.parametrize("with_endpoints", [True, False])
    @pytest.mark.parametrize("Runbook", [DslRunbookWithVariables])
    def test_publish_runbook(self, Runbook, with_secrets, with_endpoints):
        """
        test_runbook_publish_with_secret_with_endpoint_with_version
        test_runbook_publish_without_secret_with_endpoint
        test_runbook_publish_without_secret_without_endpoint
        test_runbook_publish_with_secret_without_endpoint
        """
        client = get_api_client()

        if not self.publish_runbook_uuid:
            rb_name = "test_publish_runbook_" + str(uuid.uuid4())[-10:]

            rb = upload_runbook(client, rb_name, Runbook)
            rb_state = rb["status"]["state"]
            rb_uuid = rb["metadata"]["uuid"]
            print(">> Runbook state: {}".format(rb_state))
            assert rb_state == "ACTIVE"
            assert rb_name == rb["spec"]["name"]
            assert rb_name == rb["metadata"]["name"]
            self.publish_runbook_uuid = rb_uuid

        assert self.publish_runbook_uuid is not None, "Unable to find runbook name"
        mpi_name = "test_publish_mpi_" + str(uuid.uuid4())[-10:]
        version = '1.0.0'
        print(">> Publishing mpi {} - {}, with_secrets {} and with endpoints {}".format(
            mpi_name, version, with_secrets, with_endpoints))

        mpi = publish_runbook_to_marketplace_manager(
            client,
            self.publish_runbook_uuid,
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
        assert rb_uuid == runbook_template_info['source_runbook_reference']['uuid']
        assert with_secrets == runbook_template_info.get('is_published_with_secrets', None)
        assert with_endpoints == runbook_template_info.get('is_published_with_endpoints', None)

    @pytest.mark.mpi
    @pytest.mark.regression
    @pytest.mark.parametrize("Runbook", [DslRunbookWithVariables])
    @pytest.mark.parametrize("state", [MARKETPLACE_ITEM.STATES.ACCEPTED, MARKETPLACE_ITEM.STATES.REJECTED])
    def test_approve_and_reject_runbook(self, Runbook, state):
        """
        test_marketplace_runbook_approve_market_manager
        test_reject_runbook
        """
        client = get_api_client()

        if not self.publish_runbook_uuid:
            rb_name = "test_publish_runbook_" + str(uuid.uuid4())[-10:]

            rb = upload_runbook(client, rb_name, Runbook)
            rb_state = rb["status"]["state"]
            rb_uuid = rb["metadata"]["uuid"]
            print(">> Runbook state: {}".format(rb_state))
            assert rb_state == "ACTIVE"
            assert rb_name == rb["spec"]["name"]
            assert rb_name == rb["metadata"]["name"]
            self.publish_runbook_uuid = rb_uuid

        assert self.publish_runbook_uuid is not None, "Unable to find runbook name"
        mpi_name = "test_publish_mpi_" + str(uuid.uuid4())[-10:]
        version = '1.0.0'
        print(">> Publishing mpi {} - {}".format(
            mpi_name, version))

        mpi_data = publish_runbook_to_marketplace_manager(
            client,
            self.publish_runbook_uuid,
            mpi_name,
            version,
        )
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.PENDING
        assert mpi_name == mpi_data["spec"]["name"]
        assert mpi_name == mpi_data["metadata"]["name"]

        runbook_template_info = mpi_data['status']['resources']['runbook_template_info']
        assert rb_uuid == runbook_template_info['source_runbook_reference']['uuid']

        mpi_uuid = mpi_data['metadata']['uuid']
        mpi_data = change_state(client, mpi_uuid, state)
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == state

    @pytest.mark.mpi
    @pytest.mark.regression
    @pytest.mark.parametrize("Runbook", [DslRunbookWithVariables])
    def test_mpi_different_version(self, Runbook):
        """ test_same_runbook_publish_with_secret_with_endpoint_with_different_version """
        client = get_api_client()

        if not self.publish_runbook_uuid:
            rb_name = "test_publish_runbook_" + str(uuid.uuid4())[-10:]

            rb = upload_runbook(client, rb_name, Runbook)
            rb_state = rb["status"]["state"]
            rb_uuid = rb["metadata"]["uuid"]
            print(">> Runbook state: {}".format(rb_state))
            assert rb_state == "ACTIVE"
            assert rb_name == rb["spec"]["name"]
            assert rb_name == rb["metadata"]["name"]
            self.publish_runbook_uuid = rb_uuid

        assert self.publish_runbook_uuid is not None, "Unable to find runbook name"
        mpi_name = "test_publish_mpi_" + str(uuid.uuid4())[-10:]
        version = '1.0.0'
        print(">> Publishing mpi {} - {}".format(
            mpi_name, version))

        mpi_data = publish_runbook_to_marketplace_manager(
            client,
            self.publish_runbook_uuid,
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
            rb_uuid,
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
    @pytest.mark.parametrize("Runbook", [DslRunbookWithVariables])
    def test_publish_runbook_store(self, Runbook):
        """ test_marketplace_runbook_publish_market_manager """
        client = get_api_client()

        if not self.publish_runbook_uuid:
            rb_name = "test_publish_runbook_" + str(uuid.uuid4())[-10:]

            rb = upload_runbook(client, rb_name, Runbook)
            rb_state = rb["status"]["state"]
            rb_uuid = rb["metadata"]["uuid"]
            print(">> Runbook state: {}".format(rb_state))
            assert rb_state == "ACTIVE"
            assert rb_name == rb["spec"]["name"]
            assert rb_name == rb["metadata"]["name"]
            self.publish_runbook_uuid = rb_uuid

        assert self.publish_runbook_uuid is not None, "Unable to find runbook name"
        mpi_name = "test_publish_mpi_" + str(uuid.uuid4())[-10:]
        version = '1.0.0'
        print(">> Publishing mpi {} - {}".format(
            mpi_name, version))

        mpi_data = publish_runbook_to_marketplace_manager(
            client,
            self.publish_runbook_uuid,
            mpi_name,
            version,
        )
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.PENDING
        assert mpi_name == mpi_data["spec"]["name"]
        assert mpi_name == mpi_data["metadata"]["name"]

        runbook_template_info = mpi_data['status']['resources']['runbook_template_info']
        assert rb_uuid == runbook_template_info['source_runbook_reference']['uuid']

        mpi_uuid = mpi_data['metadata']['uuid']
        mpi_data = change_state(client, mpi_uuid, MARKETPLACE_ITEM.STATES.ACCEPTED)
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.ACCEPTED

        mpi_data = change_state(client, mpi_uuid, MARKETPLACE_ITEM.STATES.PUBLISHED)
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.PUBLISHED
