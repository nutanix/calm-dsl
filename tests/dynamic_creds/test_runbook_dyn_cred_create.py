import pytest
import uuid

from calm.dsl.cli.main import get_api_client
from calm.dsl.cli.constants import RUNLOG, MARKETPLACE_ITEM
from calm.dsl.config import get_context
from tests.dynamic_creds.test_runbook_dyn_cred import (
    DslDynCredEPRunbook,
    DslDynCredRunbook,
)
from tests.api_interface.test_runbooks.utils import (
    publish_runbook_to_marketplace_manager,
    change_marketplace_state,
    execute_marketplace_runbook,
    upload_runbook,
    poll_runlog_status,
)


class TestRunbookDynCred:
    @classmethod
    def setup_class(cls):
        """Method to set dyn_cred_project in context"""

        dync_cred_project_name = "test_dyn_cred_project"

        # Setting conttext for cur tests
        ContextObj = get_context()
        ContextObj.update_project_context(dync_cred_project_name)

    @classmethod
    def teardown_class(cls):
        """Method to revert context"""

        # Setting conttext for cur tests
        ContextObj = get_context()
        ContextObj.reset_configuration()

    @pytest.mark.regression
    @pytest.mark.parametrize("Runbook", [DslDynCredEPRunbook])
    def test_rb_with_dynamic_endpoint(self, Runbook):
        """
        This routine creates a runbook with dynamic cred endpoints and executes
        """
        client = get_api_client()
        rb_name = "test_rb_" + str(uuid.uuid4())[-10:]

        rb = upload_runbook(client, rb_name, Runbook)
        rb_state = rb["status"]["state"]
        rb_uuid = rb["metadata"]["uuid"]
        print(">> Runbook state: {}".format(rb_state))
        assert rb_state == "ACTIVE"

        # run the runbook
        print("\n>>Running the runbook")
        res, err = client.runbook.run(rb_uuid, {})
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        response = res.json()
        runlog_uuid = response["status"]["runlog_uuid"]

        # polling till runbook run gets to terminal state
        state, reasons = poll_runlog_status(client, runlog_uuid, RUNLOG.TERMINAL_STATES)

        print(">> Runbook Run state: {}\n{}".format(state, reasons))
        assert state == RUNLOG.STATUS.SUCCESS

    @pytest.mark.regression
    @pytest.mark.parametrize("Runbook", [DslDynCredRunbook])
    def test_rb_with_dynamic_credentials(self, Runbook):
        """
        This routine creates a runbook with dynamic cred and executes
        """
        client = get_api_client()
        rb_name = "test_rb_" + str(uuid.uuid4())[-10:]

        rb = upload_runbook(client, rb_name, Runbook)
        rb_state = rb["status"]["state"]
        rb_uuid = rb["metadata"]["uuid"]
        print(">> Runbook state: {}".format(rb_state))
        assert rb_state == "ACTIVE"

        # run the runbook
        print("\n>>Running the runbook")
        res, err = client.runbook.run(rb_uuid, {})
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        response = res.json()
        runlog_uuid = response["status"]["runlog_uuid"]

        # polling till runbook run gets to terminal state
        state, reasons = poll_runlog_status(client, runlog_uuid, RUNLOG.TERMINAL_STATES)

        print(">> Runbook Run state: {}\n{}".format(state, reasons))
        assert state == RUNLOG.STATUS.SUCCESS

    @pytest.mark.mpi
    @pytest.mark.parametrize("Runbook", [DslDynCredEPRunbook])
    @pytest.mark.parametrize("with_endpoints", [True])
    def test_mpi_runbook_execute_same_project(self, with_endpoints, Runbook):
        """
        This routine creates a runbook with dynamic cred endpoints, publish
        runbook to marketplace and executes runbook from marketplace
        """
        client = get_api_client()
        rb_name = "test_rb_" + str(uuid.uuid4())[-10:]

        rb = upload_runbook(client, rb_name, Runbook)
        rb_state = rb["status"]["state"]
        rb_uuid = rb["metadata"]["uuid"]
        print(">> Runbook state: {}".format(rb_state))
        assert rb_state == "ACTIVE"

        mpi_name = "test_execute_mpi_" + str(uuid.uuid4())[-10:]
        version = "1.0.0"
        print(">> Publishing mpi {} - {}".format(mpi_name, version))

        mpi, err = publish_runbook_to_marketplace_manager(
            client,
            rb_uuid,
            mpi_name,
            version,
            with_endpoints=with_endpoints,
            with_secrets=True,
        )
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        mpi_data = mpi.json()
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.PENDING
        assert mpi_name == mpi_data["spec"]["name"]
        assert mpi_name == mpi_data["metadata"]["name"]

        runbook_template_info = mpi_data["status"]["resources"]["runbook_template_info"]
        assert rb_uuid == runbook_template_info["source_runbook_reference"]["uuid"]

        mpi_uuid = mpi_data["metadata"]["uuid"]
        mpi_data = change_marketplace_state(
            client, mpi_uuid, MARKETPLACE_ITEM.STATES.ACCEPTED
        )
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.ACCEPTED

        mpi_data = change_marketplace_state(
            client,
            mpi_uuid,
            MARKETPLACE_ITEM.STATES.PUBLISHED,
            project_list=["test_dyn_cred_project"],
        )
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.PUBLISHED

        endpoints_mapping = {}
        default_endpoint_uuid = None

        res, err = execute_marketplace_runbook(
            client,
            mpi_uuid,
            default_endpoint_uuid=default_endpoint_uuid,
            endpoints_mapping=endpoints_mapping,
            project_name="test_dyn_cred_project",
        )

        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        runlog_uuid = res["status"]["runlog_uuid"]

        # polling till runbook run gets to terminal state
        state, reasons = poll_runlog_status(
            client, runlog_uuid, RUNLOG.TERMINAL_STATES, maxWait=360
        )

        print(">> Runbook Run state: {}\n{}".format(state, reasons))
        assert state == RUNLOG.STATUS.SUCCESS
