import click
import sys
import traceback
from peewee import OperationalError, IntegrityError
from distutils.version import LooseVersion as LV

from calm.dsl.config import get_context
from .version import Version
from calm.dsl.db import get_db_handle, init_db_handle
from calm.dsl.log import get_logging_handle
from calm.dsl.api import get_client_handle_obj
from calm.dsl.api.util import get_auth_info

LOG = get_logging_handle(__name__)


class Cache:
    """Cache class Implementation"""

    @classmethod
    def get_cache_tables(cls, sync_version=False):
        """returns tables used for cache purpose"""

        db = get_db_handle()
        db_tables = db.registered_tables

        # Get context
        context = get_context()

        # Get calm version from api only if necessary
        calm_version = Version.get_version("Calm")
        if sync_version or (not calm_version):
            server_config = context.get_server_config()
            api_key_location = server_config.get("api_key_location", None)
            cred = get_auth_info(api_key_location)
            username = cred.get("username")
            password = cred.get("password")
            client = get_client_handle_obj(
                server_config["pc_ip"],
                server_config["pc_port"],
                auth=(username, password),
            )
            res, err = client.version.get_calm_version()
            if err:
                LOG.error("Failed to get version")
                sys.exit(err["error"])
            calm_version = res.content.decode("utf-8")

        policy_config = context.get_policy_config()
        approval_policy_config = context.get_approval_policy_config()
        cache_tables = {}
        for table in db_tables:
            if hasattr(table, "__cache_type__") and (
                LV(calm_version) >= LV(table.feature_min_version)
            ):
                if table.is_approval_policy_required:
                    # if approval policy is required check policy and approval_policy status
                    if (
                        eval(policy_config.get("policy_status", "False"))
                        == table.is_policy_required
                        and approval_policy_config.get(
                            "approval_policy_status", "False"
                        )
                        == "True"
                    ):
                        cache_tables[table.__cache_type__] = table
                elif table.is_policy_required:
                    if policy_config.get("policy_status", "False") == "True":
                        cache_tables[table.__cache_type__] = table
                else:
                    cache_tables[table.__cache_type__] = table
        return cache_tables

    @classmethod
    def get_entity_data(cls, entity_type, name, **kwargs):
        """returns entity data corresponding to supplied entry using entity name"""

        db_cls = cls.get_entity_db_table_object(entity_type)

        try:
            res = db_cls.get_entity_data(name=name, **kwargs)
        except OperationalError:
            formatted_exc = traceback.format_exc()
            LOG.debug("Exception Traceback:\n{}".format(formatted_exc))
            LOG.error(
                "Cache error occurred. Please update cache using 'calm update cache' command"
            )
            sys.exit(-1)

        if not res:
            kwargs["name"] = name
            LOG.debug(
                "Unsuccessful db query from {} table for following params {}".format(
                    entity_type, kwargs
                )
            )

        return res

    @classmethod
    def get_entity_data_using_uuid(cls, entity_type, uuid, *args, **kwargs):
        """returns entity data corresponding to supplied entry using entity uuid"""

        db_cls = cls.get_entity_db_table_object(entity_type)

        try:
            res = db_cls.get_entity_data_using_uuid(uuid=uuid, **kwargs)
        except OperationalError:
            formatted_exc = traceback.format_exc()
            LOG.debug("Exception Traceback:\n{}".format(formatted_exc))
            LOG.error(
                "Cache error occurred. Please update cache using 'calm update cache' command"
            )
            sys.exit(-1)

        if not res:
            kwargs["uuid"] = uuid
            LOG.debug(
                "Unsuccessful db query from {} table for following params {}".format(
                    entity_type, kwargs
                )
            )

        return res

    @classmethod
    def get_entity_db_table_object(cls, entity_type):
        """returns database entity table object corresponding to entity"""

        if not entity_type:
            LOG.error("No entity type for cache supplied")
            sys.exit(-1)

        cache_tables = cls.get_cache_tables()
        db_cls = cache_tables.get(entity_type, None)
        if not db_cls:
            LOG.error("Unknown entity type ({}) supplied".format(entity_type))
            sys.exit(-1)

        return db_cls

    @classmethod
    def add_one(cls, entity_type, uuid, **kwargs):
        """adds one entity to entity db object"""

        db_obj = cls.get_entity_db_table_object(entity_type)
        db_obj.add_one(uuid, **kwargs)

    @classmethod
    def delete_one(cls, entity_type, uuid, **kwargs):
        """adds one entity to entity db object"""

        db_obj = cls.get_entity_db_table_object(entity_type)
        db_obj.delete_one(uuid, **kwargs)

    @classmethod
    def update_one(cls, entity_type, uuid, **kwargs):
        """adds one entity to entity db object"""

        db_obj = cls.get_entity_db_table_object(entity_type)
        db_obj.update_one(uuid, **kwargs)

    @classmethod
    def sync(cls):
        """Sync cache by latest data"""

        def sync_tables(tables):
            for table in tables:
                try:
                    LOG.debug(
                        "Syncing cache for '{}' table".format(table.get_cache_type())
                    )
                    table.sync()
                except Exception as exp:
                    LOG.error(
                        "Cache sync failed for '{}' table".format(
                            table.get_cache_type()
                        )
                    )
                click.echo(".", nl=False, err=True)

        cache_table_map = cls.get_cache_tables(sync_version=True)
        tables = list(cache_table_map.values())

        # Inserting version table at start
        tables.insert(0, Version)

        try:
            LOG.info("Updating cache", nl=False)
            sync_tables(tables)

        except (OperationalError, IntegrityError):
            click.echo(" [Fail]")
            # init db handle once (recreating db if some schema changes are there)
            LOG.info("Removing existing db and updating cache again")
            init_db_handle()
            LOG.info("Updating cache", nl=False)
            sync_tables(tables)
        click.echo(" [Done]", err=True)

    @classmethod
    def sync_table(cls, cache_type):
        """sync the cache table provided in cache_type list"""

        if not cache_type:
            return

        cache_type = [cache_type] if not isinstance(cache_type, list) else cache_type
        cache_table_map = cls.get_cache_tables()

        for _ct in cache_type:
            if _ct not in cache_table_map:
                LOG.warning("Invalid cache_type ('{}') provided".format(cache_type))
                continue

            cache_table = cache_table_map[_ct]
            cache_table.sync()
            click.echo(".", nl=False, err=True)
        click.echo("[Done]", err=True)

    @classmethod
    def clear_entities(cls):
        """Clear data present in the cache tables"""

        # For now clearing means erasing all data. So reinitialising whole database
        init_db_handle()

    @classmethod
    def show_data(cls):
        """Display data present in cache tables"""

        cache_tables = cls.get_cache_tables()
        for cache_type, table in cache_tables.items():
            click.echo("\n{}".format(cache_type.upper()))
            try:
                table.show_data()
            except OperationalError:
                formatted_exc = traceback.format_exc()
                LOG.debug("Exception Traceback:\n{}".format(formatted_exc))
                LOG.error(
                    "Cache error occurred. Please update cache using 'calm update cache' command"
                )
                sys.exit(-1)

    @classmethod
    def show_table(cls, cache_type):
        """sync the cache table provided in cache_type list"""

        if not cache_type:
            return

        cache_type = [cache_type] if not isinstance(cache_type, list) else cache_type
        cache_table_map = cls.get_cache_tables()

        for _ct in cache_type:
            if _ct not in cache_table_map:
                LOG.warning("Invalid cache_type ('{}') provided".format(cache_type))
                continue

            cache_table = cache_table_map[_ct]
            cache_table.show_data()
