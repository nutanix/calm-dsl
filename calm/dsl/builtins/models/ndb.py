import re
import sys
import os
import pytz

from calm.dsl.log import get_logging_handle
from calm.dsl.api.handle import get_api_client
from .calm_ref import Ref
from .constants import NutanixDB as NutanixDBConst, HIDDEN_SUFFIX
from .helper import common as common_helper
from .custom_entity import CustomEntity, OutputVariables

LOG = get_logging_handle(__name__)


class DatabaseServer:
    """Database Server class for NDB includes all supported databases Server can be created"""

    name = "DatabaseServer"

    def __new__(cls, *args, **kwargs):
        raise TypeError("'{}' is not callable".format(cls.__name__))

    class Postgres:
        """Database Server class for Postgres includes all the support actions"""

        name = "Postgres_DatabaseServer"

        def __new__(cls, *args, **kwargs):
            raise TypeError("'{}' is not callable".format(cls.__name__))

        class Create(CustomEntity):
            """
            Database Server class for Postgres Create Action includes all field supported.
            Attributes supported for this class:
                name: Name of the database server,
                password: Password of the database server,
                cluster: Cluster to use for the database server,
                software_profile: Software Profile to use for the database server,
                software_profile_version: Version of the Software Profile to use for the database server,
                compute_profile: Compute Profile to use for the database server,
                network_profile: Netwrok Profile to use for the database server,
                ip_address: Static IP address for  static network profile if choosen,
                ssh_public_key:  RSA based public key to use for the database server,
                description: Description of the database server,
            """

            name = "Create_Postgres_DatabaseServer"
            DUPLICATE_KEY_MAP = {
                NutanixDBConst.Attrs.Profile.NETWORK_PROFILE: "networkprofileid",
            }
            FIELD_MAP = {
                "name": "nodes__0__vmname",
                "password": "vm_password",
                NutanixDBConst.Attrs.CLUSTER: "nxclusterid",
                NutanixDBConst.Attrs.Profile.SOFTWARE_PROFILE: "softwareprofileid",
                NutanixDBConst.Attrs.Profile.SOFTWARE_PROFILE_VERSION: "softwareprofileversionid",
                NutanixDBConst.Attrs.Profile.COMPUTE_PROFILE: "computeprofileid",
                NutanixDBConst.Attrs.Profile.NETWORK_PROFILE: "nodes__0__networkprofileid",
                "ssh_public_key": "sshpublickey",
                "description": "actionarguments__0__value",
                "ip_address": "nodes__0__ip_infos__0__ip_addresses__0",
                "description_actionargument_key"
                + HIDDEN_SUFFIX: "actionarguments__0__name",  # Not visible to users
                "ip_type"
                + HIDDEN_SUFFIX: "nodes__0__ip_infos__0__ip_type",  # Not visible to users
            }

            def pre_validate(self, account):
                """
                handles any pre_validation required such as Variable Ref compilation
                Args:
                    account (Ref.Account): Object of Calm Ref Accounts
                """

                account_name = account.name
                account_id = account.compile()["uuid"]

                # Check for ndb cluster reference
                if "nxclusterid" in self.field_values:
                    val = self.field_values["nxclusterid"]
                    common_helper.macro_or_ref_validation(
                        val,
                        Ref.NutanixDB.Cluster,
                        "cluster should be a instance of Calm Ref NutanixDB Cluster",
                    )
                    if common_helper.is_not_macro(val):
                        val.account_name = account_name
                        self.field_values["nxclusterid"] = val.compile()["uuid"]

                # Check for ndb software profile reference
                if "softwareprofileversionid" in self.field_values:
                    if "softwareprofileid" not in self.field_values:
                        raise ValueError(
                            "Software Profile is a mandatory field when Software Profile Version is given, Please provider software_profile"
                        )

                if "softwareprofileid" in self.field_values:
                    val = self.field_values["softwareprofileid"]
                    is_software_macro = True
                    common_helper.macro_or_ref_validation(
                        val,
                        Ref.NutanixDB.Profile.Software,
                        "software_profile should be a instance of Calm Ref NutanixDB Profile Software",
                    )

                    if common_helper.is_not_macro(val):
                        is_software_macro = False
                        val.engine = NutanixDBConst.PROFILE.ENGINE.POSTGRES_DATABASE
                        val.account_name = account_name
                        software_profile = val.compile()
                        self.field_values["softwareprofileid"] = software_profile[
                            "uuid"
                        ]

                    version_val = self.field_values.get("softwareprofileversionid", "")

                    # Check for ndb software version profile reference
                    if version_val:
                        common_helper.macro_or_ref_validation(
                            version_val,
                            Ref.NutanixDB.Profile.Software_Version,
                            "software_profile version should be a instance of Calm Ref NutanixDB Profile Software Version",
                        )

                        if common_helper.is_not_macro(version_val):
                            if is_software_macro:
                                raise ValueError(
                                    "software_profile version cannot be referenced when software profile is macro"
                                )

                            version_val.software_name = software_profile["name"]
                            version_val.engine = (
                                NutanixDBConst.PROFILE.ENGINE.POSTGRES_DATABASE
                            )
                            version_val.account_name = account_name
                            self.field_values[
                                "softwareprofileversionid"
                            ] = version_val.compile()

                    # Adding latest software version id if not found and software is ref
                    elif not common_helper.is_not_right_ref(
                        val, Ref.NutanixDB.Profile.Software
                    ):
                        self.field_values[
                            "softwareprofileversionid"
                        ] = software_profile["platform_data"]["latest_version_id"]

                # Check for ndb compute profile reference
                if "computeprofileid" in self.field_values:
                    val = self.field_values["computeprofileid"]
                    common_helper.macro_or_ref_validation(
                        val,
                        Ref.NutanixDB.Profile.Compute,
                        "compute_profile should be a instance of Calm Ref NutanixDB Profile Compute",
                    )
                    if common_helper.is_not_macro(val):
                        val.engine = ""
                        val.account_name = account_name
                        self.field_values["computeprofileid"] = val.compile()["uuid"]

                # Check for ndb network profile reference
                network_profile_valid = False
                ip_address_present = (
                    "nodes__0__ip_infos__0__ip_addresses__0" in self.field_values
                )

                if "nodes__0__networkprofileid" in self.field_values:
                    val = self.field_values["nodes__0__networkprofileid"]
                    common_helper.macro_or_ref_validation(
                        val,
                        Ref.NutanixDB.Profile.Network,
                        "network_profile should be a instance of Calm Ref NutanixDB Profile Network",
                    )
                    if common_helper.is_not_macro(val):
                        val.engine = NutanixDBConst.PROFILE.ENGINE.POSTGRES_DATABASE
                        val.account_name = account_name
                        network_profile = val.compile()
                        self.field_values[
                            "nodes__0__networkprofileid"
                        ] = network_profile["uuid"]
                        network_profile_valid = network_profile["platform_data"][
                            "versions"
                        ][0]["properties_map"].get("ENABLE_IP_ADDRESS_SELECTION", False)

                if ip_address_present and not network_profile_valid:
                    raise ValueError(
                        "IP Address should not be provided when network profile is not valid, static or macro"
                    )

                if ip_address_present:
                    client = get_api_client()
                    resp, err = client.resource_types.get_platform_list(
                        "Profile",
                        account_id,
                        [
                            {
                                "name": "list_available_ips_nutanix_ndb_profile__profile_id",
                                "value": self.field_values[
                                    "nodes__0__networkprofileid"
                                ],
                            }
                        ],
                        ["available_ips"],
                        "List Available IPs",
                    )
                    if err:
                        LOG.error(err)
                        sys.exit(err)
                    resp = resp.json()
                    is_address_valid = not common_helper.is_not_macro(
                        self.field_values["nodes__0__ip_infos__0__ip_addresses__0"]
                    )
                    for available_ip in resp["available_ips"]:
                        if (
                            self.field_values["nodes__0__ip_infos__0__ip_addresses__0"]
                            in available_ip["ip_addresses"]
                        ):
                            is_address_valid = True
                    if not is_address_valid:
                        raise ValueError(
                            "Please provide valid IP address for given network profile"
                        )
                    self.field_values["nodes__0__ip_infos__0__ip_type"] = "VM_IP"

                # Add actionarguments__0__name when value is present
                if "actionarguments__0__value" in self.field_values:
                    self.field_values[
                        "actionarguments__0__name"
                    ] = "dbserver_description"

        class Clone(CustomEntity):
            """
            Database class for Postgres Clone Action includes all field supported
            Attributes supported for this class:
                name: Name of the Postgres Instance,
                password: Password of the database server,
                cluster: Cluster to use for the database server,
                compute_profile: Compute Profile to use for the database server,
                network_profile: Netwrok Profile to use for the database server,
                ssh_public_key:  RSA based public key to use for the database server,
                description: Description of the database server
            """

            name = "Clone_Postgres_DatabaseServer"
            DUPLICATE_KEY_MAP = {
                NutanixDBConst.Attrs.Profile.NETWORK_PROFILE: "nodes__0__network_profile_id",
                NutanixDBConst.Attrs.CLUSTER: "nodes__0__nx_cluster_id",
                NutanixDBConst.Attrs.Profile.COMPUTE_PROFILE: "nodes__0__compute_profile_id",
                "name": "nodes__0__vm_name",
            }
            FIELD_MAP = {
                "name": "postgresql_info__0__vm_name",
                "password": "vm_password",
                NutanixDBConst.Attrs.CLUSTER: "nx_cluster_id",
                NutanixDBConst.Attrs.Profile.COMPUTE_PROFILE: "compute_profile_id",
                NutanixDBConst.Attrs.Profile.NETWORK_PROFILE: "network_profile_id",
                "ssh_public_key": "ssh_public_key",
                "description": "description",
                "node_count": "node_count",
            }

            def pre_validate(self, account):
                """
                handles any pre_validation required such as Variable Ref compilation
                Args:
                    account (Ref.Account): Object of Calm Ref Accounts
                """

                account_name = account.name

                # Check for ndb cluster reference
                if "nx_cluster_id" in self.field_values:
                    val = self.field_values["nx_cluster_id"]
                    common_helper.macro_or_ref_validation(
                        val,
                        Ref.NutanixDB.Cluster,
                        "cluster should be a instance of Calm Ref NutanixDB Cluster",
                    )
                    if common_helper.is_not_macro(val):
                        val.account_name = account_name
                        self.field_values["nx_cluster_id"] = val.compile()["uuid"]

                if "compute_profile_id" in self.field_values:
                    val = self.field_values["compute_profile_id"]
                    common_helper.macro_or_ref_validation(
                        val,
                        Ref.NutanixDB.Profile.Compute,
                        "compute_profile should be a instance of Calm Ref NutanixDB Profile Compute",
                    )
                    if common_helper.is_not_macro(val):
                        val.engine = ""
                        val.account_name = account_name
                        self.field_values["compute_profile_id"] = val.compile()["uuid"]

                if "network_profile_id" in self.field_values:
                    val = self.field_values["network_profile_id"]
                    common_helper.macro_or_ref_validation(
                        val,
                        Ref.NutanixDB.Profile.Network,
                        "network_profile should be a instance of Calm Ref NutanixDB Profile Network",
                    )
                    if common_helper.is_not_macro(val):
                        val.engine = NutanixDBConst.PROFILE.ENGINE.POSTGRES_DATABASE
                        val.account_name = account_name
                        self.field_values["network_profile_id"] = val.compile()["uuid"]

                if "node_count" not in self.field_values:
                    self.field_values["node_count"] = 1


class Database:
    """Database class for NDB includes all supported databases"""

    name = "Database"

    def __new__(cls, *args, **kwargs):
        raise TypeError("'{}' is not callable".format(cls.__name__))

    class Postgres:
        """Database class for Postgres includes all supported actions"""

        name = "Postgres_Database"

        def __new__(cls, *args, **kwargs):
            raise TypeError("'{}' is not callable".format(cls.__name__))

        class Create(CustomEntity):
            """
            Database class for Postgres Create Action includes all field supported
            Attributes supported for this class:
                name: Name of the Postgres Instance,
                description: Description of the Postgres Instance,
                database_parameter_profile: Database Parameter Profile to use for Postgres Instance,
                initial_database_name: Intial Database name to use for Postgres Instance,
                initial_database_password: Intial Database password to use for Postgres Instance,
                listener_port: Listener Port to use for Postgres Instance,
                size: Size of the Postgres Instance,
                pre_create_script: Script to run before creating the Postgres Instance,
                post_create_script: Script to run after creating the Postgres Instance,
            """

            name = "Create_Postgres_Database"
            FIELD_MAP = {
                "name": "name",
                "description": "description",
                NutanixDBConst.Attrs.Profile.DATABASE_PARAMETER_PROFILE: "dbparameterprofileid",
                "initial_database_name": "postgresql_info__0__database_names",
                "initial_database_password": "postgresql_info__0__db_password",
                "listener_port": "postgresql_info__0__listener_port",
                "size": "postgresql_info__0__database_size",
                "pre_create_script": "postgresql_info__0__pre_create_script",
                "post_create_script": "postgresql_info__0__post_create_script",
            }

            def pre_validate(self, account):
                """
                handles any pre_validation required such as Variable Ref compilation
                Args:
                    account (Ref.Account): Object of Calm Ref Accounts
                """

                account_name = account.name

                # Check for ndb database parameter profile reference
                if "dbparameterprofileid" in self.field_values:
                    val = self.field_values["dbparameterprofileid"]
                    common_helper.macro_or_ref_validation(
                        val,
                        Ref.NutanixDB.Profile.Database_Parameter,
                        "database_paramter_profile should be a instance of Calm Ref NutanixDB Database Parameter Profile",
                    )
                    if common_helper.is_not_macro(val):
                        val.engine = NutanixDBConst.PROFILE.ENGINE.POSTGRES_DATABASE
                        val.account_name = account_name
                        self.field_values["dbparameterprofileid"] = val.compile()[
                            "uuid"
                        ]

        class Delete(CustomEntity):
            """
            Database class for Postgres Delete Action includes all field supported
            Attributes supported for this class:
                database: Ref of the Postgres Instance
            """

            name = "Delete_Postgres_Database"
            FIELD_MAP = {NutanixDBConst.Attrs.DATABASE: "id"}

            def pre_validate(self, account):
                """
                handles any pre_validation required such as Variable Ref compilation
                Args:
                    account (Ref.Account): Object of Calm Ref Accounts
                """

                account_name = account.name

                if "id" in self.field_values:
                    val = self.field_values["id"]
                    common_helper.macro_or_ref_validation(
                        val,
                        Ref.NutanixDB.Database,
                        "name should be a instance of Calm Ref NutanixDB Database",
                    )
                    if common_helper.is_not_macro(val):
                        val.type = NutanixDBConst.PROFILE.ENGINE.POSTGRES_DATABASE
                        val.account_name = account_name
                        self.field_values["id"] = val.compile()["uuid"]

        class RestoreFromTimeMachine(CustomEntity):
            """
            Database class for Postgres Restore from Time Machine Action includes all field supported
            Attributes supported for this class:
                database: Name of the Postgres Instance,
                snapshot_with_timeStamp: Name of the snapshot along with TimeStamp (yyyy-mm-dd hh:mm:ss), Eg-> "era_auto_snapshot (2023-02-12 10:01:40)",
                point_in_time: point in Time to Restore yyyy-mm-dd hh:mm:ss, Eg -> "2023-02-12 10:01:40",
                time_zone: Time Zone of the snapshot/point in time (If not given defaults to system timezone),
            """

            name = "Restore_From_TimeMachine_Postgres_Database"
            FIELD_MAP = {
                NutanixDBConst.Attrs.DATABASE: "database_id",
                NutanixDBConst.Attrs.SNAPSHOT_WITH_TIMESTAMP: "snapshot_id",
                "point_in_time": "user_pitr_timestamp",
                NutanixDBConst.Attrs.TIME_ZONE: "time_zone_pitr",
            }

            def pre_validate(self, account):
                """
                handles any pre_validation required such as Variable Ref compilation
                Args:
                    account (Ref.Account): Object of Calm Ref Accounts
                """

                account_name = account.name
                time_machine_id = ""

                if "time_zone_pitr" not in self.field_values:
                    self.field_values["time_zone_pitr"] = "/".join(
                        os.path.realpath("/etc/localtime").split("/")[-2:]
                    )
                elif self.field_values["time_zone_pitr"] not in pytz.all_timezones_set:
                    LOG.error(
                        "{} is invalid, Please provide valid timezone.\nSupported timezones are {}".format(
                            self.field_values["time_zone_pitr"], pytz.all_timezones_set
                        )
                    )
                    sys.exit(-1)

                is_database_id_macro = False
                if "database_id" in self.field_values:
                    val = self.field_values["database_id"]
                    common_helper.macro_or_ref_validation(
                        val,
                        Ref.NutanixDB.Database,
                        "database should be a instance of Calm Ref NutanixDB Database",
                    )
                    if common_helper.is_not_macro(val):
                        val.type = NutanixDBConst.PROFILE.ENGINE.POSTGRES_DATABASE
                        val.account_name = account_name
                        db = val.compile()
                        time_machine_id = db["platform_data"]["time_machine_id"]
                        self.field_values["database_id"] = db["uuid"]
                    else:
                        is_database_id_macro = True

                # Either should be there.
                if (
                    "snapshot_id" in self.field_values
                    and "user_pitr_timestamp" in self.field_values
                ):
                    raise ValueError(
                        "Either of fields should be provided not both -> {}, {}".format(
                            "snapshot", "point in time (UTC)"
                        )
                    )
                if not (
                    "snapshot_id" in self.field_values
                    or "user_pitr_timestamp" in self.field_values
                ):
                    raise ValueError(
                        "Either of fields should be provided -> {}, {}".format(
                            "snapshot", "point in time (UTC)"
                        )
                    )

                if "snapshot_id" in self.field_values:
                    val = self.field_values["snapshot_id"]
                    common_helper.macro_or_ref_validation(
                        val,
                        Ref.NutanixDB.Snapshot,
                        "snapshot_with_timeStamp should be a instance of Calm Ref NutanixDB Snapshot",
                    )
                    if common_helper.is_not_macro(val):
                        if is_database_id_macro:
                            raise ValueError(
                                "snapshot_with_timeStamp cannot be referenced when database is macro"
                            )
                        name_with_timestamp = val.name
                        regex = re.compile(
                            "(.* \(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\))$"
                        )
                        if not regex.match(name_with_timestamp):
                            raise ValueError(
                                "snapshot_with_timeStamp doesn't match the format <snapshot_name> (yyyy-mm-dd hh:mm:ss)"
                            )

                        snapshot_name, timestamp = (
                            name_with_timestamp[0:-22],
                            name_with_timestamp[-20:-1],
                        )
                        timestamp = common_helper.get_timestamp_in_utc(
                            timestamp, self.field_values["time_zone_pitr"]
                        )
                        val.name = snapshot_name
                        val.snapshot_timestamp = timestamp
                        val.time_machine_id = time_machine_id
                        val.account_name = account_name
                        self.field_values["snapshot_id"] = val.compile()["uuid"]

                if (
                    "user_pitr_timestamp" in self.field_values
                    and not self.field_values["user_pitr_timestamp"]
                ):
                    raise ValueError(
                        "point_in_time should not be empty when snapshot_with_timeStamp is not given"
                    )

        class CreateSnapshot(CustomEntity):
            """
            Database class for Postgres Snapshot Action includes all field supported
            Attributes supported for this class:
                snapshot_name:           (String) Snapshot Name,
                remove_schedule_in_days: (Integer) Removal Schedule,
                time_machine:            (String) Time Machine Name,
                database:                (String) Database Name,
            """

            name = "Create_Snaphost_Postgres_Database"
            FIELD_MAP = {
                "snapshot_name": "name",
                NutanixDBConst.Attrs.TIME_MACHINE: "time_machine_id",
                NutanixDBConst.Attrs.DATABASE: "time_machine_id_from_database",
                "remove_schedule_in_days": "remove_schedule_in_days",
                "is_removal_configured"
                + HIDDEN_SUFFIX: "is_removal_configured",  # Not visible to users
            }

            def pre_validate(self, account):
                """
                handles any pre_validation required such as Variable Ref compilation
                Args:
                    account (Ref.Account): Object of Calm Ref Accounts
                """

                account_name = account.name

                # Check for timemachine reference based on database
                time_machine_id_from_database = None
                if "time_machine_id_from_database" in self.field_values:
                    val = self.field_values["time_machine_id_from_database"]
                    common_helper.macro_or_ref_validation(
                        val,
                        Ref.NutanixDB.Database,
                        "database should be a instance of Calm Ref NutanixDB Database",
                    )
                    if common_helper.is_not_macro(val):
                        val.type = NutanixDBConst.PROFILE.ENGINE.POSTGRES_DATABASE
                        val.account_name = account_name
                        time_machine_id_from_database = val.compile()["platform_data"][
                            "time_machine_id"
                        ]
                    self.field_values.pop("time_machine_id_from_database")

                # Check for ndb timemachine reference
                if "time_machine_id" in self.field_values:
                    val = self.field_values["time_machine_id"]
                    common_helper.macro_or_ref_validation(
                        val,
                        Ref.NutanixDB.TimeMachine,
                        "time_machine should be a instance of Calm Ref NutanixDB TimeMachine",
                    )
                    if common_helper.is_not_macro(val):
                        val.type = NutanixDBConst.PROFILE.ENGINE.POSTGRES_DATABASE
                        val.account_name = account_name
                        time_machine_id = val.compile()["uuid"]
                        if (
                            time_machine_id_from_database
                            and time_machine_id_from_database != time_machine_id
                        ):
                            raise Exception(
                                "Timemachine does not correspond to the provided Database"
                            )
                        self.field_values["time_machine_id"] = time_machine_id
                elif time_machine_id_from_database:
                    self.field_values["time_machine_id"] = time_machine_id_from_database

                if "remove_schedule_in_days" in self.field_values:
                    self.field_values["is_removal_configured"] = "true"

                if "time_machine_id" not in self.field_values:
                    raise ValueError(
                        "Either Time Machine or Database need to be provided"
                    )

        class Clone(CustomEntity):
            """
            Database class for Postgres Clone Action includes all field supported
            Attributes supported for this class:
                name: Name of the Postgres Instance,
                description: Description of the Postgres Instance,
                password: Password of the Postgres Instance,
                database_parameter_profile: Database Parameter Profile to use for Postgres Instance,
                pre_clone_cmd: Script to run before creating the Postgres Instance,
                post_clone_cmd: Script to run after creating the Postgres Instance,
            """

            name = "Clone_Postgres_Database"

            FIELD_MAP = {
                "name": "name",
                "description": "description",
                NutanixDBConst.Attrs.Profile.DATABASE_PARAMETER_PROFILE: "database_parameter_profile_id",
                "password": "postgresql_info__0__db_password",
                "pre_clone_cmd": "postgresql_info__0__pre_clone_cmd",
                "post_clone_cmd": "postgresql_info__0__post_clone_cmd",
            }

            def pre_validate(self, account):
                """
                handles any pre_validation required such as Variable Ref compilation
                Args:
                    account (Ref.Account): Object of Calm Ref Accounts
                """

                account_name = account.name

                # Check for ndb database parameter profile reference
                if "database_parameter_profile_id" in self.field_values:
                    val = self.field_values["database_parameter_profile_id"]
                    common_helper.macro_or_ref_validation(
                        val,
                        Ref.NutanixDB.Profile.Database_Parameter,
                        "database_paramter_profile should be a instance of Calm Ref NutanixDB Database Parameter Profile",
                    )
                    if common_helper.is_not_macro(val):
                        val.engine = NutanixDBConst.PROFILE.ENGINE.POSTGRES_DATABASE
                        val.account_name = account_name
                        self.field_values[
                            "database_parameter_profile_id"
                        ] = val.compile()["uuid"]


class TimeMachine:
    """TimeMachine class for NDB includes all supported databases"""

    name = "TimeMachine"

    def __new__(cls, *args, **kwargs):
        raise TypeError("'{}' is not callable".format(cls.__name__))

    class Postgres:
        """TimeMachine class for Postgres includes all supported actions"""

        name = "Postgres_TimeMachine"

        def __new__(cls, *args, **kwargs):
            raise TypeError("'{}' is not callable".format(cls.__name__))

        class Create(CustomEntity):
            """
            TimeMachine class for Postgres Create Action includes all field supported
            Attributes supported for this class:
                name: Name of the Time Machine,
                description: Description of the Time Machine,
                sla: SLA to use for the Time Machine,
                snapshottimeofday__hours: Hour of the day to take Snapshot,
                snapshottimeofday__minutes: Minute of the day to take Snapshot,
                snapshottimeofday__seconds: Second of the day to take Snapshot,
                snapshots_perday: Snapshots to take Per day,
                logbackup_interval: Log Backup Interval in minutes,
                weeklyschedule__dayofweek: Weekly Snapshot day of the week,
                monthlyschedule__dayofmonth: Monthly Snaphot day of the month,
                quartelyschedule__startmonth: Quarterly Snapshot start of the month,
            """

            name = "Create_Postgres_TimeMachine"
            FIELD_MAP = {
                "name": "timemachineinfo__0__name",
                "description": "timemachineinfo__0__description",
                NutanixDBConst.Attrs.SLA: "timemachineinfo__0__slaid",
                "snapshottimeofday__hours": "timemachineinfo__0__schedule__0__snapshottimeofday__0__hours",
                "snapshottimeofday__minutes": "timemachineinfo__0__schedule__0__snapshottimeofday__0__minutes",
                "snapshottimeofday__seconds": "timemachineinfo__0__schedule__0__snapshottimeofday__0__seconds",
                "snapshots_perday": "timemachineinfo__0__schedule__0__continuousschedule__0__snapshotsperday",
                "logbackup_interval": "timemachineinfo__0__schedule__0__continuousschedule__0__logbackupinterval",
                "weeklyschedule__dayofweek": "timemachineinfo__0__schedule__0__weeklyschedule__0__dayofweek",
                "monthlyschedule__dayofmonth": "timemachineinfo__0__schedule__0__monthlyschedule__0__dayofmonth",
                "quartelyschedule__startmonth": "timemachineinfo__0__schedule__0__quartelyschedule__0__startmonth",
            }

            def pre_validate(self, account):
                """
                handles any pre_validation required such as Variable Ref compilation
                Args:
                    account (Ref.Account): Object of Calm Ref Accounts
                """

                account_name = account.name

                # Check for ndb sla reference

                if "timemachineinfo__0__slaid" in self.field_values:
                    val = self.field_values["timemachineinfo__0__slaid"]
                    common_helper.macro_or_ref_validation(
                        val,
                        Ref.NutanixDB.SLA,
                        "sla should be a instance of Calm Ref NutanixDB SLA",
                    )
                    if common_helper.is_not_macro(val):
                        val.account_name = account_name
                        sla = val.compile()
                        self.field_values["timemachineinfo__0__slaid"] = sla["uuid"]

                        disabled_fields = []

                        # check for fields which are enabled according to the SLA
                        def sla_disabled_fields_validation(key, fields):
                            if sla[key] == 0:
                                for field in fields:
                                    if self.FIELD_MAP[field] in self.field_values:
                                        disabled_fields.append(field)

                        sla_disabled_fields_validation(
                            "daily_retention",
                            [
                                "snapshottimeofday__hours",
                                "snapshottimeofday__minutes",
                                "snapshottimeofday__seconds",
                                "continuousschedule__snapshotsperday",
                            ],
                        )

                        sla_disabled_fields_validation(
                            "continuous_retention",
                            ["continuousschedule__logbackupinterval"],
                        )

                        sla_disabled_fields_validation(
                            "weekly_retention", ["weeklyschedule__dayofweek"]
                        )

                        sla_disabled_fields_validation(
                            "monthly_retention", ["monthlyschedule__dayofmonth"]
                        )

                        sla_disabled_fields_validation(
                            "quartely_retention",
                            ["quartelyschedule__startmonth"],
                        )

                        if disabled_fields:
                            raise ValueError(
                                "Given SLA {} doesn't allow values for following given fields: {}".format(
                                    sla["name"], disabled_fields
                                )
                            )

        class Clone(CustomEntity):
            """
            TimeMachine class for Postgres Clone Action includes all field supported
            Attributes supported for this class:
                time_machine: Name of the Time Machine,
                snapshot_with_timeStamp: Name of the snapshot along with TimeStamp (yyyy-mm-dd hh:mm:ss), Eg-> "era_auto_snapshot (2023-02-12 10:01:40)",
                point in time: point in Time to Restore yyyy-mm-dd hh:mm:ss, Eg -> "2023-02-12 10:01:40",
                time_zone: Time Zone of the snapshot/point in time (If not given defaults to system timezone),
                expiry_days: Number of days to expire,
                expiry_date_timezone : Timezone to be used for expiry date,
                delete_database: Boolean input for deletion of database,
                refresh_in_days: Number of days to refresh,
                refresh_time: Time at which refresh should trigger,
                refresh_date_timezone: Timezone for the refresh time,
            """

            name = "Clone_Postgres_TimeMachine"
            FIELD_MAP = {
                NutanixDBConst.Attrs.TIME_MACHINE: "time_machine_id",
                NutanixDBConst.Attrs.SNAPSHOT_WITH_TIMESTAMP: "snapshot_id",
                "point_in_time": "user_pitr_timestamp",
                NutanixDBConst.Attrs.TIME_ZONE: "time_zone",
                "expiry_days": "lcm_config__0__database_lcm_config__0__expiry_details__0__expire_in_days",
                "expiry_date_timezone": "lcm_config__0__database_lcm_config__0__expiry_details__0__expiry_date_timezone",
                "delete_database": "lcm_config__0__database_lcm_config__0__expiry_details__0__delete_database",
                "refresh_in_days": "lcm_config__0__database_lcm_config__0__refresh_details__0__refresh_in_days",
                "refresh_time": "lcm_config__0__database_lcm_config__0__refresh_details__0__refresh_time",
                "refresh_date_timezone": "lcm_config__0__database_lcm_config__0__refresh_details__0__refresh_date_timezone",
                "schedule_data_refresh"
                + HIDDEN_SUFFIX: "schedule_data_refresh",  # Not visible to users
                "remove_schedule"
                + HIDDEN_SUFFIX: "remove_schedule",  # Not visible to users
            }

            def pre_validate(self, account):
                """
                handles any pre_validation required such as Variable Ref compilation
                Args:
                    account (Ref.Account): Object of Calm Ref Accounts
                """

                if "time_zone" not in self.field_values:
                    self.field_values["time_zone"] = "/".join(
                        os.path.realpath("/etc/localtime").split("/")[-2:]
                    )
                elif self.field_values["time_zone"] not in pytz.all_timezones_set:
                    LOG.error(
                        "{} is invalid, Please provide valid timezone.\nSupported timezones are {}".format(
                            self.field_values["time_zone"], pytz.all_timezones_set
                        )
                    )
                    sys.exit(-1)

                if (
                    "snapshot_id" in self.field_values
                    and "user_pitr_timestamp" in self.field_values
                ):
                    raise ValueError(
                        "Either of fields should be provided not both -> {}, {}".format(
                            "snapshot", "point in time (UTC)"
                        )
                    )
                elif not (
                    "snapshot_id" in self.field_values
                    or "user_pitr_timestamp" in self.field_values
                ):
                    raise ValueError(
                        "Either of fields should be provided -> {}, {}".format(
                            "snapshot", "point in time (UTC)"
                        )
                    )

                account_name = account.name
                is_time_machine_id_macro = False

                if "time_machine_id" in self.field_values:
                    val = self.field_values["time_machine_id"]
                    common_helper.macro_or_ref_validation(
                        val,
                        Ref.NutanixDB.TimeMachine,
                        "time_machine_name should be a instance of Calm Ref NutanixDB TimeMachine",
                    )
                    if common_helper.is_not_macro(val):
                        val.account_name = account_name
                        val.type = NutanixDBConst.PROFILE.ENGINE.POSTGRES_DATABASE
                        self.field_values["time_machine_id"] = val.compile()["uuid"]
                    else:
                        is_time_machine_id_macro = True

                if "snapshot_id" in self.field_values:
                    val = self.field_values["snapshot_id"]
                    common_helper.macro_or_ref_validation(
                        val,
                        Ref.NutanixDB.Snapshot,
                        "snapshot_with_timeStamp should be a instance of Calm Ref NutanixDB Snapshot",
                    )
                    if common_helper.is_not_macro(val):
                        if is_time_machine_id_macro:
                            raise ValueError(
                                "snapshot_with_timeStamp cannot be referenced when database is macro"
                            )
                        name_with_timestamp = val.name
                        regex = re.compile(
                            "(.* \(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\))$"
                        )
                        if not regex.match(name_with_timestamp):
                            raise ValueError(
                                "snapshot_with_timeStamp doesn't match the format <snapshot_name> (yyyy-mm-dd hh:mm:ss)"
                            )

                        snapshot_name, timestamp = (
                            name_with_timestamp[0:-22],
                            name_with_timestamp[-20:-1],
                        )
                        timestamp = common_helper.get_timestamp_in_utc(
                            timestamp, self.field_values["time_zone"]
                        )
                        val.name = snapshot_name
                        val.snapshot_timestamp = timestamp
                        val.time_machine_id = self.field_values["time_machine_id"]
                        val.account_name = account_name
                        self.field_values["snapshot_id"] = val.compile()["uuid"]

                if (
                    "user_pitr_timestamp" in self.field_values
                    and not self.field_values["user_pitr_timestamp"]
                ):
                    raise ValueError(
                        "point_in_time should not be empty when snapshot_with_timeStamp is not given"
                    )

                if (
                    "lcm_config__0__database_lcm_config__0__expiry_details__0__expire_in_days"
                    in self.field_values
                    or "lcm_config__0__database_lcm_config__0__expiry_details__0__delete_database"
                    in self.field_values
                ):
                    self.field_values["remove_schedule"] = "true"

                if (
                    "lcm_config__0__database_lcm_config__0__refresh_details__0__refresh_in_days"
                    in self.field_values
                    or "lcm_config__0__database_lcm_config__0__refresh_details__0__refresh_time"
                    in self.field_values
                ):
                    self.field_values["schedule_data_refresh"] = "true"


class Tag:
    """Tag class for NDB includes all supported tags"""

    name = "Tag"

    def __new__(cls, *args, **kwargs):
        raise TypeError("'{}' is not callable".format(cls.__name__))

    class Create(CustomEntity):
        """
        Tag class for Create Action includes all field supported
        Attributes supported for this class:
            database: array of NDB Database Tag Ref. Eg -> [ Ref.NutanixDB.Tag.Database(name1, value1), Ref.NutanixDB.Tag.Database(name=name2, value=value2) ],
            time_machine: array of NDB TimeMachine Tag Ref. Eg -> [ Ref.NutanixDB.Tag.TimeMachine(name=name1, value=value1), Ref.NutanixDB.Tag.TimeMachine(name2, value2) ],
        """

        name = "Create_Tag"
        FIELD_MAP = {
            NutanixDBConst.Attrs.Tag.DATABASE: "tags",
            NutanixDBConst.Attrs.Tag.TIME_MACHINE: "timemachineinfo__0__tags",
        }

        def pre_validate(self, account):
            """
            handles any pre_validation required such as Variable Ref compilation
            Args:
                account (Ref.Account): Object of Calm Ref Accounts
            """

            account_name = account.name

            # Check for database tags reference
            if "tags" in self.field_values:
                vals = self.field_values["tags"]
                if not isinstance(vals, list):
                    raise ValueError("Tags should be array of Tag Database Ref")

                tag_dict_list = []
                for val in vals:
                    if isinstance(val, Ref.NutanixDB.Tag.Database):
                        raise ValueError(
                            "{} should be instance of database tag".format(val)
                        )

                    val.account_name = account_name
                    tag_dict_list.append(val.compile())

                self.field_values["tags"] = tag_dict_list

            # Check for time machinetags reference
            if "timemachineinfo__0__tags" in self.field_values:
                vals = self.field_values["timemachineinfo__0__tags"]
                if not isinstance(vals, list):
                    raise ValueError("Tags should be array of Tag TIME_MACHINE Ref")

                tag_dict_list = []
                for val in vals:
                    if isinstance(val, Ref.NutanixDB.Tag.TimeMachine):
                        raise ValueError(
                            "{} should be instance of TimeMachine tag".format(val)
                        )

                    val.account_name = account_name
                    tag_dict_list.append(val.compile())

                self.field_values["timemachineinfo__0__tags"] = tag_dict_list

    class Clone(CustomEntity):
        """
        Tag class for Clone Action includes all field supported
        Attributes supported for this class:
            clone: array of NDB Clone Tag Ref. Eg -> [ Ref.NutanixDB.Tag.Clone(name1, value1), Ref.NutanixDB.Tag.Clone(name=name2, value=value2) ]
        """

        name = "Clone_Tag"
        FIELD_MAP = {
            NutanixDBConst.Attrs.Tag.CLONE: "tags",
        }

        def pre_validate(self, account):
            """
            handles any pre_validation required such as Variable Ref compilation
            Args:
                account (Ref.Account): Object of Calm Ref Accounts
            """

            account_name = account.name

            # Check for clone tags reference
            if "tags" in self.field_values:
                vals = self.field_values["tags"]
                if not isinstance(vals, list):
                    raise ValueError("Tags should be array of Tag Clone Ref")

                tag_dict_list = []
                for val in vals:
                    if isinstance(val, Ref.NutanixDB.Tag.Clone):
                        raise ValueError(
                            "{} should be instance of Clone tag".format(val)
                        )

                    val.account_name = account_name
                    tag_dict_list.append(val.compile())

                self.field_values["tags"] = tag_dict_list


class PostgresDatabaseOutputVariables:
    """Base Class for Postgres Database Instance Actions Output variables of NDB Provider (Not Callable)"""

    name = "Postgres_OutputVariables"

    def __new__(cls, *args, **kwargs):
        raise TypeError("'{}' is not callable".format(cls.__name__))

    class Create(OutputVariables):
        """
        Postgres Database Instance Create Action Output variables of NDB Provider, user can provide mapping for the name of this attributes that can be used as alias to it.
        Attributes supported for this class:
            database_name: Name of the database instance
            database_instance_id: ID of database instance created
            tags: A tag is a label consisting of a user-defined name and a value that makes it easier to manage, search for, and filter entities
            properties: Properties of the entity, Eg -> Database instance, database, profiles
            time_machine: Time machine details when an instance is created
            time_machine_id: UUID of time machine
            metric: Stores storage info regarding size, allocatedSize, usedSize and unit of calculation that have been fetched from PRISM
            type: The type of the database created i.e., postgres_database
            platform_data: Platform data is the aggregate data of all the output variables supported
        """

        name = "Create_Postgres_OutputVariables"
        FIELD_MAP = {
            "database_name": "database_name",
            "database_instance_id": "database_instance_id",
            "tags": "tags",
            "properties": "properties",
            "time_machine": "time_machine",
            "time_machine_id": "time_machine_id",
            "metric": "metric",
            "type": "type",
            "platform_data": "platform_data",
        }

    class RestoreFromTimeMachine(OutputVariables):
        """
        Postgres Database Instance RestoreFromTimeMachine Action Output variables of NDB Provider, user can provide mapping for the name of this attributes that can be used as alias to it.
        Attributes supported for this class:
            database_name: Name of the database instance
            database_instance_id: ID of database instance created
            tags: A tag is a label consisting of a user-defined name and a value that makes it easier to manage, search for, and filter entities
            properties: Properties of the entity, Eg -> Database instance, database, profiles
            time_machine: Time machine details when an instance is created
            time_machine_id: UUID of time machine
            metric: Stores storage info regarding size, allocatedSize, usedSize and unit of calculation that seems to have been fetched from PRISM
            type: The type of the database created i.e., postgres_database
            platform_data: Platform data is the aggregate data of all the output variables supported
        """

        name = "RestoreFromTimeMachine_Postgres_OutputVariables"
        FIELD_MAP = {
            "database_name": "database_name",
            "database_instance_id": "database_instance_id",
            "tags": "tags",
            "properties": "properties",
            "time_machine": "time_machine",
            "time_machine_id": "time_machine_id",
            "metric": "metric",
            "type": "type",
            "platform_data": "platform_data",
        }

    class CreateSnapshot(OutputVariables):
        """
        Postgres Database Instance CreateSnapshot Action Output variables of NDB Provider.
        User can provide mapping for the name of this attributes that can be used as alias to it.

        Attributes supported for this class:
            database_snapshot: Snapshot of the database
            properties: Properties of the entity, Eg -> Database instance, database, profiles
            dbserver_name: Name of the database server VM
            type: The type of the database created i.e., postgres_database
            dbserver_ip: IP address of the database server VM
            id: ID of database instance created
            parent_snapshot: Snapshot used to clone the database
            snapshot_uuid: Uuid of the Snapshot
            platform_data: Platform data is the aggregate data of all the output variables supported
        """

        name = "Create_Snapshot_Postgres_OutputVariables"
        FIELD_MAP = {
            "database_snapshot": "database_snapshot",
            "properties": "properties",
            "dbserver_name": "dbserver_name",
            "type": "type",
            "dbserver_ip": "dbserver_ip",
            "id": "id",
            "parent_snapshot": "parent_snapshot",
            "snapshot_uuid": "snapshot_uuid",
            "platform_data": "platform_data",
        }

    class Clone(OutputVariables):
        """
        Postgres Database Instance Clone Action Output variables of NDB Provider
        User can provide mapping for the name of this attributes that can be used as alias to it.

        Attributes supported for this class:
            type: The type of the database created i.e., postgres_database
            id: ID of database instance created
            time_machine: Time machine details when an instance is created
            linked_databases: These are databases which are created as a part of the instance
            database_name: Name of the database instance
            database_nodes: Info of nodes of databases
            platform_data: Platform data is the aggregate data of all the output variables supported
        """

        name = "Clone_Postgres_OutputVariables"

        FIELD_MAP = {
            "type": "type",
            "id": "id",
            "time_machine": "time_machine",
            "linked_databases": "linked_databases",
            "database_name": "database_name",
            "database_nodes": "database_nodes",
            "platform_data": "platform_data",
        }
