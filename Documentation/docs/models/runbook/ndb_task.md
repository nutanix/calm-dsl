# Nutanix Database (NDB)

- NDB models represents the attributes required for performing various Database operations
- NDB models available in DSL are Database, DatabaseServer, TimeMachine and Tag. They are further divided into different subclasses based on specific operations
- NDB model also constitute of OutputVariable Model which give user leverage to set task variables for the output variables.

## DatabaseServer:
    
This model provides attributes for the server related information. This is divided into different subclasses which inherits from Postgres DatabaseServer, a subclass to DatabaseServer.

- Postgres:
        
    This model provides attributes for performing various operations on Postgres Databases.

    - Create:
        - Model Definition:
            ```
            from calm.dsl.builtins.models.ndb import DatabaseServer

            DatabaseServer.Postgres.Create(
                name="db_server_name",
                password="db_server_password",
                cluster=Ref.NutanixDB.Cluster(name="EraCluster"),
                software_profile=Ref.NutanixDB.Profile.Software(name="POSTGRES_10.4_OOB"),
                software_profile_version=Ref.NutanixDB.Profile.Software_Version(
                    name="POSTGRES_10.4_OOB (1.0)"
                ),
                compute_profile=Ref.NutanixDB.Profile.Compute(name="DEFAULT_OOB_COMPUTE"),
                network_profile=Ref.NutanixDB.Profile.Network(
                    name="DEFAULT_OOB_POSTGRESQL_NETWORK"
                ),
                ip_address="10.44.76.141",
                ssh_public_key="ssh_key for the server",
                description="Sample description of db server",
            )
            ```

        - Attributes supported for this class:
            1. **name**: (String) Name of the database server
            2. **password**: (String) Password of the database server
            3. **cluster**: (NDB Ref/ Macro) Cluster to use for the database server
            4. **software_profile**: (NDB Ref/ Macro) Software Profile to use for the database server
            5. **software_profile_version**: (NDB Ref/ Macro) Version of the Software Profile to use for the database server
            6. **compute_profile**: (NDB Ref/ Macro) Compute Profile to use for the database server
            7. **network_profile**: (NDB Ref/ Macro) Network Profile to use for the database server
            8. **ip_address**: (String) Static IP address for  static network profile if provided
            9. **ssh_public_key**:  (String) RSA based public key to use for the database server
            10. **description**: (String) Description of the database server
    
    - Clone:
        - Model Definition:
            ```
            from calm.dsl.builtins.models.ndb import DatabaseServer

            DatabaseServer.Postgres.Clone(
                name="new_db_@@{calm_time}@@",
                password="abc123",
                cluster=Ref.NutanixDB.Cluster(name="EraCluster"),
                compute_profile=Ref.NutanixDB.Profile.Compute(name="DEFAULT_OOB_COMPUTE"),
                network_profile=Ref.NutanixDB.Profile.Network(
                    name="DEFAULT_OOB_POSTGRESQL_NETWORK"
                ),
                ssh_public_key="ssh-key",
                description="Sample description of db server",
            )
            ```
        
        - Attributes supported for this class:
            1. **name**: (String) Name of the Postgres Instance
            2. **password**: (String) Password of the database server
            3. **cluster**: (NDB Ref/ Macro) Cluster to use for the database server
            4. **compute_profile**: (NDB Ref/ Macro) Compute Profile to use for the database server
            5. **network_profile**: (NDB Ref/ Macro) Network Profile to use for the database server
            6. **ssh_public_key**:  (String) RSA based public key to use for the database server
            7. **description**: (String) Description of the database server

## Database:
    
This model provides attributes for the database instance related information. This is divided into different subclasses which inherits from Postgres Database, a subclass to Database.

- Postgres:
    
    This model provides attributes for performing various operations on Postgres Databases.

    - Create:
        - Model Definition:
            ```
            from calm.dsl.builtins.models.ndb import Database

            Database.Postgres.Create(
                name="post_inst_@@{calm_time}@@",
                description="Sample description of postgres instances",
                database_parameter_profile=Ref.NutanixDB.Profile.Database_Parameter(
                    name="DEFAULT_POSTGRES_PARAMS"
                ),
                initial_database_name="TEST_DB_01",
                initial_database_password="DB_PASS",
                listener_port="5432",
                size="200",
                pre_create_script="",
                post_create_script="",
            )
            ```
        
        - Attributes supported for this class:
            1. **name**: (String) Name of the Postgres Instance
            2. **description**: (String) Description of the Postgres Instance
            3. **database_parameter_profile**: (NDB Ref/ Macro) Database Parameter Profile to use for Postgres Instance
            4. **initial_database_name**: (String) Intial Database name to use for Postgres Instance
            5. **initial_database_password**: (String) Intial Database password to use for Postgres Instance
            6. **listener_port**: (Integer) Listener Port to use for Postgres Instance
            7. **size**: (Integer) Size of the Postgres Instance
            8. **pre_create_script**: (String) Script to run before creating the Postgres Instance
            9. **post_create_script**: (String) Script to run after creating the Postgres Instance
    
    - Delete:
        - Model Definition:
            ```
            from calm.dsl.builtins.models.ndb import Database

            Database.Postgres.Delete(
                name=Ref.NutanixDB.Database(name="bekkam-pg-dnd")
            )
            ```
        
        - Attributes supported for this class:
            1. **database**: (NDB Ref/ Macro) Ref of the Postgres Instance
    
    - Create Snapshot:
        - Model Definition:
            ```
            from calm.dsl.builtins.models.ndb import Database

            Database.Postgres.CreateSnapshot(
                snapshot_name="snap-from-dsl",
                remove_schedule_in_days=2,
                # time_machine="@@{tm_uuid}@@",
                time_machine=Ref.NutanixDB.TimeMachine(name="dnd-pg_TM"),
                database=Ref.NutanixDB.Database(name="dnd-pg"),
            )
            ```
        
        - Attributes supported for this class:
            1. **snapshot_name**:           (String) Snapshot Name
            2. **remove_schedule_in_days**: (Integer) Removal Schedule
            3. **time_machine**:            (NDB Ref/ Macro) Time Machine Name
            4. **database**:                (NDB Ref/ Macro) Database Name
    
    - Restore From Time Machine:
        - Model Definition:
            ```
            from calm.dsl.builtins.models.ndb import Database

            Database.Postgres.RestoreFromTimeMachine(
                database=Ref.NutanixDB.Database("test-pg-inst"),
                snapshot_with_timeStamp=Ref.NutanixDB.Snapshot(
                "era_auto_snapshot (2023-03-01 14:46:17)"
                ),
                time_zone="America/Resolute",
                #point_in_time="2023-02-12 10:01:40",
            )
            ```
        
        - Attributes supported for this class:
            1. **database**: (NDB Ref/ Macro) Name of the Postgres Instance
            2. **snapshot_with_timeStamp**: (NDB Ref/ Macro) Name of the snapshot along with TimeStamp (yyyy-mm-dd hh:mm:ss) Eg-> "era_auto_snapshot (2023-02-12 10:01:40)"
            3. **point_in_time**: (String) point in Time to Restore yyyy-mm-dd hh:mm:ss Eg -> "2023-02-12 10:01:40"
            4. **time_zone**: (String) Time Zone of the snapshot/point in time (If not given defaults to system timezone)

        - Note: Either of snapshot_with_timeStamp and point_in_time can be specified

    - Clone:
        - Model Definition:
            ```
            from calm.dsl.builtins.models.ndb import Database

            Database.Postgres.Clone(
                name="post_inst_@@{calm_time}@@",
                database_parameter_profile=Ref.NutanixDB.Profile.Database_Parameter(
                    name="DEFAULT_POSTGRES_PARAMS"
                ),
                password="Nutanix.123",
                pre_clone_cmd="",
                post_clone_cmd="",
            )
            ```
        
        - Attributes supported for this class:
            1. **name**: (String) Name of the Postgres Instance
            2. **description**: (String) Description of the Postgres Instance
            3. **password**: (String) Password of the Postgres Instance
            4. **database_parameter_profile**: (NDB Ref/ Macro) Database Parameter Profile to use for Postgres Instance
            5. **pre_clone_cmd**: (String) Script to run before creating the Postgres Instance
            6. **post_clone_cmd**: (String) Script to run after creating the Postgres Instance

## TimeMachine:
    
This model provides attributes for the timeMachine related information. This is divided into different subclasses which inherits from Postgres TimeMachine, a subclass to TimeMachine.

- Postgres:
    
    This model provides attributes for performing various operations on Postgres Databases.

    - Create:
        - Model Definition:
            ```
            from calm.dsl.builtins.models.ndb import TimeMachine

            TimeMachine.Postgres.Create(
                name="inst_@@{calm_time}@@_TM",
                description="This is time machine's description",
                sla=Ref.NutanixDB.SLA(name="DEFAULT_OOB_GOLD_SLA"),
                snapshottimeofday__hours=12,
                snapshottimeofday__minutes=0,
                snapshottimeofday__seconds=0,
                snapshots_perday=1,
                logbackup_interval=60,
                weeklyschedule__dayofweek="WEDNESDAY",
                monthlyschedule__dayofmonth=17,
                quartelyschedule__startmonth="FEBRUARY",
            )
            ```
        
        - Attributes supported for this class:
            1. **name**: (String) Name of the Time Machine
            2. **description**: (String) Description of the Time Machine
            3. **sla**: (NDB Ref/ Macro) SLA to use for the Time Machine
            4. **snapshottimeofday__hours**: (Integer) Hour of the day to take Snapshot
            5. **snapshottimeofday__minutes**: (Integer) Minute of the day to take Snapshot
            6. **snapshottimeofday__seconds**: (Integer) Second of the day to take Snapshot
            7. **snapshots_perday**: (Integer) Snapshots to take Per day
            8. **logbackup_interval**: (Integer) Log Backup Interval in minutes
            9. **weeklyschedule__dayofweek**: (String) Weekly Snapshot day of the week
            10. **monthlyschedule__dayofmonth**:  (Integer) Monthly Snaphot day of the month
            11. **quartelyschedule__startmonth**: (String) Quarterly Snapshot start of the month
    
    - Clone:
        - Model Definition:
            ```
            from calm.dsl.builtins.models.ndb import TimeMachine

            TimeMachine.Postgres.Clone(
                time_machine_name=Ref.NutanixDB.TimeMachine("dnd-tm2"),
                point_in_time="2023-02-12 10:01:40",
                <!-- snapshot_with_timeStamp=Ref.NutanixDB.Snapshot(
                "era_auto_snapshot (2023-03-23 20:01:46)"
                ), -->
                time_zone="UTC",
            )
            ```
        
        - Attributes supported for this class:
            1. **time_machine**: (NDB Ref/ Macro) Name of the Time Machine
            2. **snapshot_with_timeStamp**: (NDB Ref/ Macro) Name of the snapshot along with TimeStamp (yyyy-mm-dd hh:mm:ss) Eg-> "era_auto_snapshot (2023-02-12 10:01:40)"
            3. **point in time**: (String) point in Time to Restore yyyy-mm-dd hh:mm:ss Eg -> "2023-02-12 10:01:40"
            4. **time_zone**: (String) Time Zone of the snapshot/point in time (If not given defaults to system timezone)
            5. **expiry_days**: (Integer) Number of days to expire
            6. **expiry_date_timezone** : (String) Timezone to be used for expiry date
            7. **delete_database**: (Boolean) Boolean input for deletion of database
            8. **refresh_in_days**: (Integer) Number of days to refresh
            9. **refresh_time**: (String) Time at which refresh should trigger
            10. **refresh_date_timezone**: (String) Timezone for the refresh time

        - Note: Either of snapshot_with_timeStamp and point_in_time can be specified

## Tag:
    
This model provides attributes for the tag related information. This is divided into different subclasses wrt to the Actions.

- Create:
    - Model Definition:
        ```
        from calm.dsl.builtins.models.ndb import Tag

        Tag.Create(
            database_tags=[
                DatabaseTag("prod_database", "true"),
                DatabaseTag("database_type", "Postgres"),
            ],
            time_machine_tags=[
                TimemachineTag("type", "gold"),
            ],
        )
        ```
        
    - Attributes supported for this class:
        1. **database**: ([NDB Ref]) array of NDB Database Tag Ref. Eg -> [ Ref.NutanixDB.Tag.Database(name1, value1), Ref.NutanixDB.Tag.Database(name=name2, value=value2) ]
        2. **time_machine**: ([NDB Ref]) array of NDB TimeMachine Tag Ref. Eg -> [ Ref.NutanixDB.Tag.TimeMachine(name=name1, value=value1), Ref.NutanixDB.Tag.TimeMachine(name2, value2) ]

- Clone:
    - Model Definition:
        ```
        from calm.dsl.builtins.models.ndb import Tag

        Tag.Clone(tags=[CloneTag("tag name", "")])
        ```
        
    - Attributes supported for this class:
        1. **clone**: ([NDB Ref]) array of NDB Clone Tag Ref. Eg -> [ Ref.NutanixDB.Tag.Clone(name1, value1), Ref.NutanixDB.Tag.Clone(name=name2, value=value2) ]

## PostgresDatabaseOutputVariables:

This model provides information about the output variables associated to postgres actions.
        
- Create:
    - Model Definition:
        ```
        from calm.dsl.builtins.models.ndb import PostgresDatabaseOutputVariables

        PostgresDatabaseOutputVariables.Create(
            database_name="postgres_database_name",
            database_instance_id="",
            tags="",
            properties="",
            time_machine="postgres_time_machine",
            time_machine_id="",
            metric="",
            type="",
            platform_data="",
        )
        ```
        
    - Attributes supported for this class:
        1. **database_name**: (String) Name of the database instance
        2. **database_instance_id**: (String) ID of database instance created
        3. **tags**: ([Dict]) A tag is a label consisting of a user-defined name and a value that makes it easier to manage, search for, and filter entities
        4. **properties**:  ([Dict]) Properties of the entity, Eg -> Database instance, database, profiles
        5. **time_machine**: (Dict) Time machine details when an instance is created
        6. **time_machine_id**:(String) UUID of time machine
        7. **metric**: (Dict) Stores storage info regarding size, allocatedSize, usedSize and unit of calculation that have been fetched from PRISM
        8. **type**: (String) The type of the database created i.e., postgres_database
        9. **platform_data**: (Dict) Platform data is the aggregate data of all the output variables supported 

- Create Snapshot:
    - Model Definition:
        ```
        from calm.dsl.builtins.models.ndb import PostgresDatabaseOutputVariables

        PostgresDatabaseOutputVariables.CreateSnapshot(
            platform_data='myplatformdata'
        )
        ```
        
    - Attributes supported for this class:
        1. **database_snapshot**: (Dict) Snapshot of the database
        2. **properties**: (Dict) Properties of the entity, Eg -> Database instance, database, profiles
        3. **dbserver_name**: (String) Name of the database server VM
        4. **type**: (String) The type of the database created i.e., postgres_database
        5. **dbserver_ip**: (String) IP address of the database server VM
        6. **id**: (String) ID of database instance created
        7. **parent_snapshot**: (Dict) Snapshot used to clone the database
        8. **snapshot_uuid**: (String) Uuid of the Snapshot
        9. **platform_data**: (Dict) Platform data is the aggregate data of all the output  variables supported

- Restore From Time Machine:
    - Model Definition:
        ```
        from calm.dsl.builtins.models.ndb import PostgresDatabaseOutputVariables

        PostgresDatabaseOutputVariables.RestoreFromTimeMachine(
            database_name="postgres_database_name",
            database_instance_id="",
            tags="",
            properties="",
            time_machine="postgres_time_machine",
            time_machine_id="",
            metric="",
            type="",
            platform_data="",
        )
        ```
        
    - Attributes supported for this class:
        1. **database_name**: (String) Name of the database instance
        2. **database_instance_id**: (String) ID of database instance created
        3. **tags**: ([Dict]) A tag is a label consisting of a user-defined name and a value that makes it easier to manage, search for, and filter entities
        4. **properties**: (Dict) Properties of the entity, Eg -> Database instance, database, profiles
        5. **time_machine**: (Dict) Time machine details when an instance is created
        6. **time_machine_id**: (String) UUID of time machine
        7. **metric**: (Dict) Stores storage info regarding size, allocatedSize, usedSize and unit of calculation that seems to have been fetched from PRISM
        8. **type**: (String) The type of the database created i.e., postgres_database
        9. **platform_data**: (Dict) Platform data is the aggregate data of all the output variables supported

- Clone:
    - Model Definition:
        ```
        from calm.dsl.builtins.models.ndb import PostgresDatabaseOutputVariables

        PostgresDatabaseOutputVariables.Clone(
            id="postgres_Clone_id"
        )
        ```
        
    - Attributes supported for this class:
        1. **type**: (String) The type of the database created i.e., postgres_database
        2. **id**: (String)  ID of database instance created
        3. **time_machine**: (Dict) Time machine details when an instance is created
        4. **linked_databases**: ([String]) These are databases which are created as a part of the instance
        5. **database_name**: (String) Name of the database instance
        6. **database_nodes**: ([Dict]) Info of nodes of databases
        7. **platform_data**: (Dict) Platform data is the aggregate data of all the output variables supported
