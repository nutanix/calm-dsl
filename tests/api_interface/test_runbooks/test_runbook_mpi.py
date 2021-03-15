import pytest
import uuid
from distutils.version import LooseVersion as LV

from calm.dsl.store import Version
from calm.dsl.cli.main import get_api_client
from calm.dsl.cli.constants import RUNLOG, MARKETPLACE_ITEM

# from test_files.marketplace_runbook import DslRunbookForMPI, create_project_endpoints
from test_files.marketplace_runbook import (
    DslRunbookForMPI,
    DslWhileDecisionRunbookForMPI,
)
from utils import (
    publish_runbook_to_marketplace_manager,
    change_marketplace_state,
    clone_marketplace_runbook,
    execute_marketplace_runbook,
    upload_runbook,
    poll_runlog_status,
    validate_error_message,
)

# calm_version
CALM_VERSION = Version.get_version("Calm")


@pytest.mark.skipif(
    LV(CALM_VERSION) < LV("3.2.0"),
    reason="Tests are for env changes introduced in 3.2.0",
)
class TestMarketplaceRunbook:
    @classmethod
    def setup_class(cls):
        """
        Creating Runbooks and Endpoints to test runbook sharing
        """

        client = get_api_client()
        cls.runbook_name = "test_publish_runbook_" + str(uuid.uuid4())[-10:]
        rb = upload_runbook(client, cls.runbook_name, DslRunbookForMPI)
        rb_state = rb["status"]["state"]
        rb_uuid = rb["metadata"]["uuid"]
        print(">> Runbook state: {}".format(rb_state))
        cls.runbook_uuid = rb_uuid

        cls.default_project_endpoints = {}
        endpoint_uuids = []
        default_endpoint_uuid = (
            rb["status"]["resources"]
            .get("default_target_reference", {})
            .get("uuid", "")
        )
        if default_endpoint_uuid:
            res, err = client.endpoint.read(default_endpoint_uuid)
            ep = res.json()
            ep_type = ep["spec"]["resources"]["type"]
            ep_name = ep["spec"]["name"]
            cls.default_project_endpoints[ep_type] = (ep_name, default_endpoint_uuid)
            endpoint_uuids.append(default_endpoint_uuid)
            cls.default_endpoint_details = {
                "uuid": default_endpoint_uuid,
                "type": ep_type,
                "name": ep_name,
            }

        for task in rb["status"]["resources"]["runbook"]["task_definition_list"]:
            ep_uuid = task.get("target_any_local_reference", {}).get("uuid", "")
            if ep_uuid and ep_uuid not in endpoint_uuids:
                res, err = client.endpoint.read(ep_uuid)
                ep = res.json()
                ep_type = ep["spec"]["resources"]["type"]
                ep_name = ep["spec"]["name"]
                cls.default_project_endpoints[ep_type] = (ep_name, ep_uuid)
                endpoint_uuids.append(ep_uuid)

        # Will be added once setup changes landed
        # cls.second_project_name, cls.second_project_endpoints = create_project_endpoints(client)

    @pytest.mark.runbook
    @pytest.mark.mpi
    @pytest.mark.regression
    @pytest.mark.parametrize("with_secrets", [True, False])
    @pytest.mark.parametrize("with_endpoints", [True, False])
    def test_publish_runbook(self, with_secrets, with_endpoints):
        """
        test_runbook_publish_with_secret_with_endpoint
        test_runbook_publish_without_secret_with_endpoint
        test_runbook_publish_without_secret_without_endpoint
        test_runbook_publish_with_secret_without_endpoint
        """
        print(
            "Testing RB publish with_ep {}, with_secret {}".format(
                with_endpoints, with_secrets
            )
        )
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
        version = "1.0.0"
        print(
            ">> Publishing mpi {} - {}, with_secrets {} and with endpoints {}".format(
                mpi_name, version, with_secrets, with_endpoints
            )
        )

        mpi, err = publish_runbook_to_marketplace_manager(
            client,
            self.runbook_uuid,
            mpi_name,
            version,
            with_secrets=with_secrets,
            with_endpoints=with_endpoints,
        )

        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        mpi_data = mpi.json()
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == "PENDING"
        assert mpi_name == mpi_data["spec"]["name"]
        assert mpi_name == mpi_data["metadata"]["name"]

        runbook_template_info = mpi_data["status"]["resources"]["runbook_template_info"]
        assert (
            self.runbook_uuid
            == runbook_template_info["source_runbook_reference"]["uuid"]
        )
        assert with_secrets == runbook_template_info.get(
            "is_published_with_secrets", None
        )
        assert with_endpoints == runbook_template_info.get(
            "is_published_with_endpoints", None
        )

    @pytest.mark.runbook
    @pytest.mark.mpi
    @pytest.mark.regression
    @pytest.mark.parametrize(
        "state", [MARKETPLACE_ITEM.STATES.ACCEPTED, MARKETPLACE_ITEM.STATES.REJECTED]
    )
    def test_approve_and_reject_runbook_marketplace(self, state):
        """
        test_marketplace_runbook_approve_market_manager
        test_marketplace_runbook_reject_market_manager
        test_delete_marketplace_runbook
        """
        print("Testing MPI {}".format(state))
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
        version = "1.0.0"
        print(">> Publishing mpi {} - {}".format(mpi_name, version))

        mpi, err = publish_runbook_to_marketplace_manager(
            client,
            self.runbook_uuid,
            mpi_name,
            version,
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
        assert (
            self.runbook_uuid
            == runbook_template_info["source_runbook_reference"]["uuid"]
        )

        mpi_uuid = mpi_data["metadata"]["uuid"]
        mpi_data = change_marketplace_state(client, mpi_uuid, state)
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == state

        # TEST DELETE MPI
        res, err = client.market_place.delete(uuid=mpi_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

    @pytest.mark.runbook
    @pytest.mark.mpi
    @pytest.mark.regression
    def test_same_name_mpi_with_different_version(self):
        """test_same_name_mpi_with_different_version"""

        print("Testing RB publish with different versions")
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
        version = "1.0.0"
        print(">> Publishing mpi {} - {}".format(mpi_name, version))

        mpi, err = publish_runbook_to_marketplace_manager(
            client,
            self.runbook_uuid,
            mpi_name,
            version,
        )
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        mpi_data = mpi.json()
        mpi_uuid = mpi_data["metadata"]["uuid"]
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
        print(
            ">> Publishing mpi {} - {}, with_secrets {} and with endpoints {}".format(
                mpi_name, new_mpi_version, with_secrets, with_endpoints
            )
        )

        new_mpi, err = publish_runbook_to_marketplace_manager(
            client,
            self.runbook_uuid,
            mpi_name,
            new_mpi_version,
            with_secrets=with_secrets,
            with_endpoints=with_endpoints,
            app_group_uuid=app_group_uuid,
        )
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        new_mpi_data = new_mpi.json()
        new_mpi_uuid = new_mpi_data["metadata"]["uuid"]
        new_mpi_state = new_mpi_data["status"]["resources"]["app_state"]
        print(">> New MPI state: {}".format(new_mpi_state))
        assert new_mpi_state == MARKETPLACE_ITEM.STATES.PENDING
        assert mpi_name == new_mpi_data["spec"]["name"]
        assert mpi_name == new_mpi_data["metadata"]["name"]
        assert new_mpi_version == new_mpi_data["status"]["resources"]["version"]

        new_app_group_uuid = new_mpi_data["status"]["resources"]["app_group_uuid"]
        assert app_group_uuid == new_app_group_uuid

        runbook_template_info = new_mpi_data["status"]["resources"][
            "runbook_template_info"
        ]
        assert with_secrets == runbook_template_info.get(
            "is_published_with_secrets", None
        )
        assert with_endpoints == runbook_template_info.get(
            "is_published_with_endpoints", None
        )

        # DELETE MPI
        res, err = client.market_place.delete(uuid=mpi_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        res, err = client.market_place.delete(uuid=new_mpi_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

    @pytest.mark.runbook
    @pytest.mark.mpi
    @pytest.mark.regression
    def test_publish_unshare_unpublish_runbook_store(self):
        """
        test_marketplace_runbook_publish_market_manager
        test_marketplace_manager_share_project
        test_marketplace_manager_unshare_project
        test_marketplace_runbook_unpublish
        """
        print(
            "Testing MPI publish and share to store and unshare and unplish from store"
        )

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
        version = "1.0.0"
        print(">> Publishing mpi {} - {}".format(mpi_name, version))

        mpi, err = publish_runbook_to_marketplace_manager(
            client,
            self.runbook_uuid,
            mpi_name,
            version,
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
        assert (
            self.runbook_uuid
            == runbook_template_info["source_runbook_reference"]["uuid"]
        )

        mpi_uuid = mpi_data["metadata"]["uuid"]
        mpi_data = change_marketplace_state(
            client, mpi_uuid, MARKETPLACE_ITEM.STATES.ACCEPTED
        )
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.ACCEPTED

        # TEST PUBLISH AND SHARE
        projects_shared_with = ["default"]
        mpi_data = change_marketplace_state(
            client,
            mpi_uuid,
            MARKETPLACE_ITEM.STATES.PUBLISHED,
            project_list=projects_shared_with,
        )
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.PUBLISHED

        for project_ref in mpi_data["status"]["resources"]["project_reference_list"]:
            project_name = project_ref.get("name", "")
            assert (
                project_name in projects_shared_with
            ), "Marketplace shared with some other project"

        # TEST UNSHARE FROM PROJECT
        mpi_data = change_marketplace_state(
            client, mpi_uuid, MARKETPLACE_ITEM.STATES.PUBLISHED, project_list=[]
        )

        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.PUBLISHED

        project_list = mpi_data["status"]["resources"].get("project_reference_list", [])
        assert len(project_list) == 0, "Marketplace item still shared with some project"

        # TEST UNPUBLISH
        mpi_data = change_marketplace_state(
            client, mpi_uuid, MARKETPLACE_ITEM.STATES.ACCEPTED
        )
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.ACCEPTED

        # DELETE MPI
        res, err = client.market_place.delete(uuid=mpi_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

    @pytest.mark.ces
    @pytest.mark.runbook
    @pytest.mark.mpi
    @pytest.mark.regression
    @pytest.mark.parametrize("with_endpoints", [True, False])
    def test_mpi_runbook_clone_same_project(self, with_endpoints):
        """
        test_marketplace_runbook_with_endpoint_clone_same_project
        test_marketplace_runbook_without_endpoint_clone_same_project
        """

        print("Testing MPI clone in same project with_ep {}".format(with_endpoints))
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
        version = "1.0.0"
        print(">> Publishing mpi {} - {}".format(mpi_name, version))

        mpi, err = publish_runbook_to_marketplace_manager(
            client,
            self.runbook_uuid,
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
        assert (
            self.runbook_uuid
            == runbook_template_info["source_runbook_reference"]["uuid"]
        )

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
            project_list=["default"],
        )
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.PUBLISHED

        cloned_rb_name = self.runbook_name + "_cloned_" + str(uuid.uuid4())[-10:]
        res, err = clone_marketplace_runbook(
            client, mpi_uuid, cloned_rb_name, project_name="default"
        )

        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        cloned_runbook_uuid = res["runbook_uuid"]

        res, err = client.runbook.read(cloned_runbook_uuid)

        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        cloned_rb = res.json()
        cloned_rb_state = cloned_rb["status"]["state"]

        assert cloned_rb_name == cloned_rb["spec"]["name"]
        assert cloned_rb_name == cloned_rb["metadata"]["name"]

        print(">> Runbook state: {}".format(cloned_rb_state))
        if with_endpoints:
            assert (
                cloned_rb_state == "ACTIVE"
            ), "Runbook published with endpoints should be in Active state"
        else:
            assert (
                cloned_rb_state == "DRAFT"
            ), "Runbook published without endpoints should be in Draft state"

    @pytest.mark.skip(
        reason="different project tests will be enabled after setup lands on master"
    )
    @pytest.mark.runbook
    @pytest.mark.mpi
    @pytest.mark.regression
    @pytest.mark.parametrize("with_endpoints", [True, False])
    def test_mpi_runbook_clone_different_project(self, with_endpoints):
        """
        test_marketplace_runbook_with_endpoint_clone_different_project
        test_marketplace_runbook_without_endpoint_clone_different_project
        """
        print(
            "Testing MPI clone in different project with_ep {}".format(with_endpoints)
        )
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
        version = "1.0.0"
        print(">> Publishing mpi {} - {}".format(mpi_name, version))

        mpi, err = publish_runbook_to_marketplace_manager(
            client,
            self.runbook_uuid,
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
        assert (
            self.runbook_uuid
            == runbook_template_info["source_runbook_reference"]["uuid"]
        )

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
            project_list=[self.second_project_name],
        )
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.PUBLISHED

        cloned_rb_name = self.runbook_name + "_cloned_" + str(uuid.uuid4())[-10:]
        res, err = clone_marketplace_runbook(
            client, mpi_uuid, cloned_rb_name, project_name=self.second_project_name
        )
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        cloned_runbook_uuid = res["runbook_uuid"]

        res, err = client.runbook.read(cloned_runbook_uuid)

        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        cloned_rb = res.json()
        cloned_rb_state = cloned_rb["status"]["state"]

        assert cloned_rb_name == cloned_rb["spec"]["name"]
        assert cloned_rb_name == cloned_rb["metadata"]["name"]

        print(">> Runbook state: {}".format(cloned_rb_state))
        assert (
            cloned_rb_state == "DRAFT"
        ), "Runbook published without endpoints should be in Draft state"

    @pytest.mark.ces
    @pytest.mark.runbook
    @pytest.mark.mpi
    @pytest.mark.regression
    @pytest.mark.parametrize("with_endpoints", [True, False])
    def test_mpi_runbook_execute_same_project(self, with_endpoints):
        """
        test_marketplace_runbook_with_endpoint_execute_same_project
        test_marketplace_runbook_without_endpoint_execute_same_project
        """
        print("Testing MPI execute in same project with_ep {}".format(with_endpoints))
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
        version = "1.0.0"
        print(">> Publishing mpi {} - {}".format(mpi_name, version))

        mpi, err = publish_runbook_to_marketplace_manager(
            client,
            self.runbook_uuid,
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
        assert (
            self.runbook_uuid
            == runbook_template_info["source_runbook_reference"]["uuid"]
        )

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
            project_list=["default"],
        )
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.PUBLISHED

        endpoints_mapping = {}
        default_endpoint_uuid = None
        if not with_endpoints:
            for ep_name, ep_uuid in self.default_project_endpoints.values():
                endpoints_mapping[ep_name] = ep_uuid
            default_endpoint_uuid = self.default_endpoint_details.get("uuid", None)

        res, err = execute_marketplace_runbook(
            client,
            mpi_uuid,
            default_endpoint_uuid=default_endpoint_uuid,
            endpoints_mapping=endpoints_mapping,
            project_name="default",
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

    @pytest.mark.skip(
        reason="different project tests will be enabled after setup lands on master"
    )
    @pytest.mark.runbook
    @pytest.mark.mpi
    @pytest.mark.regression
    @pytest.mark.parametrize("with_endpoints", [True, False])
    def test_mpi_runbook_execute_different_project(self, with_endpoints):
        """
        test_marketplace_runbook_with_endpoint_execute_different_project
        test_marketplace_runbook_without_endpoint_execute_different_project
        """
        print(
            "Testing MPI execute in different project with_ep {}".format(with_endpoints)
        )
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
        version = "1.0.0"
        print(">> Publishing mpi {} - {}".format(mpi_name, version))

        mpi, err = publish_runbook_to_marketplace_manager(
            client,
            self.runbook_uuid,
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
        assert (
            self.runbook_uuid
            == runbook_template_info["source_runbook_reference"]["uuid"]
        )

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
            project_list=[self.second_project_name],
        )
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.PUBLISHED

        endpoints_mapping = {}
        default_endpoint_uuid = None
        if not with_endpoints:
            for ep_type, ep_info in self.default_project_endpoints.items():
                second_project_ep_info = self.second_project_endpoints.get(ep_type)
                endpoints_mapping[ep_info[0]] = second_project_ep_info[1]

            default_endpoint_type = self.default_endpoint_details.get("type")
            default_endpoint_uuid = self.second_project_endpoints[
                default_endpoint_type
            ][1]

        res, err = execute_marketplace_runbook(
            client,
            mpi_uuid,
            default_endpoint_uuid=default_endpoint_uuid,
            endpoints_mapping=endpoints_mapping,
            project_name=self.second_project_name,
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

    @pytest.mark.runbook
    @pytest.mark.mpi
    @pytest.mark.regression
    def test_mpi_list_with_type(self):
        """
        test_mpi_list_with_type
        """
        print("Testing MPI list with filters")
        client = get_api_client()

        mpi_params = {
            "filter": "type=={}".format(MARKETPLACE_ITEM.TYPES.RUNBOOK),
            "length": 20,
        }
        res, err = client.market_place.list(params=mpi_params)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        response = res.json()
        mpi_entities = response.get("entities", [])

        for mpi in mpi_entities:
            assert (
                mpi["status"]["type"] == MARKETPLACE_ITEM.TYPES.RUNBOOK
            ), "MPI not of type runbook"

    @pytest.mark.ces
    @pytest.mark.runbook
    @pytest.mark.regression
    @pytest.mark.mpi
    @pytest.mark.parametrize("with_secrets", [True, False])
    def test_mpi_runbook_variables(self, with_secrets):
        """
        test_marketplace_runbook_with_secret_execute_variables
        test_marketplace_runbook_without_secret_execute_variables
        """

        print("Testing variables in MPI execute with_secrets {}".format(with_secrets))
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
        version = "1.0.0"
        print(">> Publishing mpi {} - {}".format(mpi_name, version))

        mpi, err = publish_runbook_to_marketplace_manager(
            client,
            self.runbook_uuid,
            mpi_name,
            version,
            with_endpoints=True,
            with_secrets=with_secrets,
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
        assert (
            self.runbook_uuid
            == runbook_template_info["source_runbook_reference"]["uuid"]
        )

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
            project_list=["default"],
        )
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.PUBLISHED

        if with_secrets:
            args = [
                {"name": "var2", "value": "no"},
                {"name": "firstname", "value": "Mr X"},
                {"name": "lastname", "value": "Y"},
            ]

            expected_output = "xxxx\nyes\nxx\nxx\nHello Mr X LASTNAME\n"
        else:
            args = [
                {"name": "var2", "value": "no"},
                {"name": "firstname", "value": "Mr X"},
                {"name": "lastname", "value": "Y"},
            ]
            expected_output = "\nxx\nxx\nxx\nHello Mr X LASTNAME\n"

        res, err = execute_marketplace_runbook(
            client, mpi_uuid, args=args, project_name="default"
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

        # Finding the task_uuid for the exec task
        res, err = client.runbook.list_runlogs(runlog_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        response = res.json()
        entities = response["entities"]
        for entity in entities:
            if (
                entity["status"]["type"] == "task_runlog"
                and entity["status"]["task_reference"]["name"] == "ES_Task"
            ):
                exec_task = entity["metadata"]["uuid"]

        # Now checking the output of exec task
        print("runlog_id: {}".format(runlog_uuid))
        res, err = client.runbook.runlog_output(runlog_uuid, exec_task)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        runlog_output = res.json()
        output_list = runlog_output["status"]["output_list"]

        print("ouput of the task: {}".format(output_list[0]["output"]))
        assert output_list[0]["output"] == expected_output

    @pytest.mark.runbook
    @pytest.mark.mpi
    @pytest.mark.regression
    def test_neg_runbook_marketplace(self):
        """
        test_neg_runbook_publish_empty_name
        test_neg_runbook_publish_empty_version
        test_neg_mpi_runbook_execute_without_mapping
        test_neg_mpi_runbook_clone_without_name
        test_neg_mpi_runbook_execute_deleted_mpi
        test_neg_mpi_runbook_clone_deleted_mpi
        """
        print("Testing Negative runbook mpi test cases")
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
        version = "1.0.0"

        print("Neg testing publish without name")
        mpi, err = publish_runbook_to_marketplace_manager(
            client,
            self.runbook_uuid,
            marketplace_item_name="",
            version=version,
        )
        if not err:
            print("Publish of runbook without name is successful")
            pytest.fail("Publish of runbook without name is successful")

        validate_error_message(err["error"], "name is empty")

        print("Neg testing publish without version")
        mpi, err = publish_runbook_to_marketplace_manager(
            client,
            self.runbook_uuid,
            marketplace_item_name=mpi_name,
            version="",
        )
        if not err:
            print("Publish of runbook without version is successful")
            pytest.fail("Publish of runbook without version is successful")

        validate_error_message(err["error"], "version is a required field")

        print(">> Publishing mpi {} - {}".format(mpi_name, version))

        mpi, err = publish_runbook_to_marketplace_manager(
            client, self.runbook_uuid, mpi_name, version, with_endpoints=False
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
        assert (
            self.runbook_uuid
            == runbook_template_info["source_runbook_reference"]["uuid"]
        )

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
            project_list=["default"],
        )
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.PUBLISHED

        print("Neg testing clone without name")
        res, err = clone_marketplace_runbook(
            client, mpi_uuid, runbook_name="", project_name="default"
        )
        if not err:
            print("Clone of mpi without runbook name is successful")
            pytest.fail("Clone of mpi without runbook name is successful")

        validate_error_message(err["error"], "name cannot be empty")

        print("Neg testing execute without endpoint mapping")
        res, err = execute_marketplace_runbook(client, mpi_uuid, project_name="default")

        if not err:
            print("Execute of mpi without endpoint mappping is successful")
            pytest.fail("Execute of mpi without endpoint mappping is successful")

        validate_error_message(err["error"], "unable to find mapping for endpoint")

        # Unplish MPI
        mpi_data = change_marketplace_state(
            client, mpi_uuid, MARKETPLACE_ITEM.STATES.ACCEPTED, project_list=[]
        )
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.ACCEPTED

        # TEST DELETE MPI
        res, err = client.market_place.delete(uuid=mpi_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        print("Neg testing clone of deleted mpi")
        res, err = clone_marketplace_runbook(
            client, mpi_uuid, runbook_name="rb", project_name="default"
        )
        if not err:
            print("Clone of deleted mpi is successful")
            pytest.fail("Clone of deleted mpi is successful")

        validate_error_message(err["error"], "entity does not exist")

        print("Neg testing execute of delete mpi")
        res, err = execute_marketplace_runbook(client, mpi_uuid, project_name="default")

        if not err:
            print("Execute of deleted mpi is successful")
            pytest.fail("Execute of deleted mpi is successful")

        validate_error_message(err["error"], "entity does not exist")

    @pytest.mark.runbook
    @pytest.mark.regression
    def test_mpi_while_decision(self):
        """ test_while_macro_in_iteration_count"""

        client = get_api_client()
        rb_name = "test_while_macro_" + str(uuid.uuid4())[-10:]

        rb = upload_runbook(client, rb_name, DslWhileDecisionRunbookForMPI)
        rb_state = rb["status"]["state"]
        rb_uuid = rb["metadata"]["uuid"]
        print(">> Runbook state: {}".format(rb_state))
        assert rb_state == "ACTIVE"
        assert rb_name == rb["spec"]["name"]
        assert rb_name == rb["metadata"]["name"]

        # endpoints generated by this runbook
        endpoint_list = rb["spec"]["resources"].get("endpoint_definition_list", [])

        mpi_name = "test_execute_while_decision_mpi_" + str(uuid.uuid4())[-10:]
        version = "1.0.0"
        print(">> Publishing mpi {} - {}".format(mpi_name, version))

        mpi, err = publish_runbook_to_marketplace_manager(
            client, rb_uuid, mpi_name, version, with_endpoints=True, with_secrets=True
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
            project_list=["default"],
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
            project_name="default",
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

        # Check iteration in while task runlog
        res, err = client.runbook.list_runlogs(runlog_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        response = res.json()
        entities = response["entities"]
        for entity in entities:
            if entity["status"]["type"] == "task_runlog":
                task_name = entity["status"]["task_reference"]["name"]
                if task_name == "WhileTask":
                    assert entity["status"]["iterations"] == "3"

            if (
                entity["status"]["type"] == "task_runlog"
                and entity["status"]["task_reference"]["name"] == "FAILURE"
            ):
                pytest.fail(
                    "[{}] path should not get executed".format(
                        entity["status"]["task_reference"]["name"]
                    )
                )

        mpi_data = change_marketplace_state(
            client, mpi_uuid, MARKETPLACE_ITEM.STATES.ACCEPTED
        )
        mpi_state = mpi_data["status"]["resources"]["app_state"]
        print(">> MPI state: {}".format(mpi_state))
        assert mpi_state == MARKETPLACE_ITEM.STATES.ACCEPTED

        # DELETE MPI
        res, err = client.market_place.delete(uuid=mpi_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        _, err = client.runbook.delete(rb_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        else:
            print("runbook {} deleted".format(rb_name))

        # delete endpoints generated by this test
        for endpoint in endpoint_list:
            _, err = client.endpoint.delete(endpoint["uuid"])
            if err:
                pytest.fail("[{}] - {}".format(err["code"], err["error"]))
