# Calm-DSL supports Nutanix Database (NDB) operations in Runbook for Postgres Databases:

1. Ability to Create, Delete PostgreSQL Database VMs and it's instances on NDB.
2. Ability to Create Snapshot of Existing Postgres Databases on NDB. 
3. Ability to Restore Database Instance using a existing snapshot or point in time snapshot on NDB. 
4. Ability to Clone a Existing Postgres VM and it's instance on NDB. 

Checkout the [Blog](https://next.nutanix.com/community-blog-154/unlock-the-simplicity-exploring-the-nutanix-database-service-ndb-and-nutanix-cloud-manager-ncm-self-service-integration-42140) for feature details in Self Service

## NDB Entity Cache support:

- User can use `calm show cache -e <entity_name>` helper to look for the existing NDB entities cached in Calm-DSL database
- NDB Entities supported in cache
    1. Database: User can use `ndb_database` as entity_name to get the existing postgres databases in NDB.
    2. Profile: User can use `ndb_profile` as entity_name to get the existing profiles in NDB.
    3. SLA: User can use `ndb_sla` as entity_name to get the existing SLAs in NDB.
    4. Cluster: User can use `ndb_cluster` as entity_name to get the existing clusters in NDB.
    5. Time Machine: User can use `ndb_timemachine` as entity_name to get the existing time machines compatible to Postgres Database in NDB.
    6. Snapshot: User can use `ndb_snapshot` as entity_name to get the existing Snapshots compatible to Postgres Database in NDB.
    7. Tag: User can use  `ndb_tag` as entity_name to get the existing tags in NDB.

## Create Task:

- User can use `Task.NutanixDB.PostgresDatabase.Create()` helper to create NDB Create Action Task. 
- Look [here](../../examples/Runbooks/NutanixDB_runbooks/postgresDB_create.py) for example.

    ```
    Task.NutanixDB.PostgresDatabase.Create(
        name="postgres_create_task_name",
        account=Ref.Account("NDB"),
        database_server_config=database_server_params(),
        instance_config=postgresinstance_params(),
        timemachine_config=timemachine_params(),
        tag_config=tag_params(),
        outargs=output_variables(),
    )
    ```

### database_server_config

- Use `database_server_config` to provide database server params required for Postgres Create Action

- Use `DatabaseServer.Postgres.Create()` in NDB models to create database server config

    ```
    def database_server_params():
        """Get the Database server config for postgres create action"""
        return DatabaseServer.Postgres.Create(
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
    1. name: Name of the database server
    2. password: Password of the database server
    3. cluster: Cluster to use for the database server
    4. software_profile: Software Profile to use for the database server
    5. software_profile_version: Version of the Software Profile to use for the database server
    6. compute_profile: Compute Profile to use for the database server
    7. network_profile: Netwrok Profile to use for the database server
    8. ip_address: Static IP address for  static network profile if choosen
    9. ssh_public_key:  RSA based public key to use for the database server
    10. description: Description of the database server


### instance_config

- Use `instance_config` to provide database instance params required for Postgres Create Action

- Use `Database.Postgres.Create()` in NDB models to create instance_config

    ```
    def postgresinstance_params():
        """Get the postgres instance config for postgres create action runbook update"""
        return Database.Postgres.Create(
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
    1. name: Name of the Postgres Instance
    2. description: Description of the Postgres Instance
    3. database_parameter_profile: Database Parameter Profile to use for Postgres Instance
    4. initial_database_name: Intial Database name to use for Postgres Instance
    5. initial_database_password: Intial Database password to use for Postgres Instance
    6. listener_port: Listener Port to use for Postgres Instance
    7. size: Size of the Postgres Instance
    8. pre_create_script: Script to run before creating the Postgres Instance
    9. post_create_script: Script to run after creating the Postgres Instance


### timemachine_config

- Use `timemachine_config` to provide time machine params required for Postgres Create Action

- Use `TimeMachine.Postgres.Create()` in NDB models to create timemachine_config

    ```
    def timemachine_params():
        """Get the Time Machine config for postgres create action"""
        return TimeMachine.Postgres.Create(
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
    1. name: Name of the Time Machine
    2. description: Description of the Time Machine
    3. sla: SLA to use for the Time Machine
    4. snapshottimeofday__hours: Hour of the day to take Snapshot
    5. snapshottimeofday__minutes: Minute of the day to take Snapshot
    6. snapshottimeofday__seconds: Second of the day to take Snapshot
    7. snapshots_perday: Snapshots to take Per day
    8. logbackup_interval: Log Backup Interval in minutes
    9. weeklyschedule__dayofweek: Weekly Snapshot day of the week
    10. monthlyschedule__dayofmonth: Monthly Snaphot day of the month
    11. quartelyschedule__startmonth: Quarterly Snapshot start of the month

### tag_config

- Use `tag_config` to provide tag params required for Postgres Create Action

- Use `Tag.Create()` in NDB models to create tag_config

    ```
    DatabaseTag = Ref.NutanixDB.Tag.Database
    TimemachineTag = Ref.NutanixDB.Tag.TimeMachine

    def tag_params():
        """Get the Tag config for postgres create action"""
        return Tag.Create(
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
    1. database: array of NDB Database Tag Ref. Eg -> [ Ref.NutanixDB.Tag.Database(name1, value1), Ref.NutanixDB.Tag.Database(name=name2, value=value2) ]
    2. time_machine: array of NDB TimeMachine Tag Ref. Eg -> [ Ref.NutanixDB.Tag.TimeMachine(name=name1, value=value1), Ref.NutanixDB.Tag.TimeMachine(name2, value2) ]

### outargs

- Use `outargs` to provide output variable params required for Postgres Create Action

- Use `PostgresDatabaseOutputVariables.Create()` in NDB models to create outargs

    ```
    def output_variables():
        """Get the defined output variable mapping for postgres create action"""
        return PostgresDatabaseOutputVariables.Create(
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
    1. database_name: Name of the database instance
    2. database_instance_id: ID of database instance created
    3. tags: A tag is a label consisting of a user-defined name and a value that makes it easier to manage, search for, and filter entities
    4. properties: Properties of the entity, Eg -> Database instance, database, profiles
    5. time_machine: Time machine details when an instance is created
    6. time_machine_id: UUID of time machine
    7. metric: Stores storage info regarding size, allocatedSize, usedSize and unit of calculation that have been fetched from PRISM
    8. type: The type of the database created i.e., postgres_database
    9. platform_data: Platform data is the aggregate data of all the output variables supported


## Delete Task:

- User can use `Task.NutanixDB.PostgresDatabase.Delete()` helper to create NDB Delete Action Task.
- Look [here](../../examples/Runbooks/NutanixDB_runbooks/postgresDB_delete.py) for example.

    ```
    Task.NutanixDB.PostgresDatabase.Delete(
        name="task_name",
        account=Ref.Account("era1"),
        instance_config=postgresinstance_params()
    )
    ```

### instance_config

- Use `instance_config` to provide database instance params required for Postgres Delete Action

- Use `Database.Postgres.Delete()` in NDB models to create instance_config

    ```
    def postgresinstance_params():
        """Get the postgres instance config for postgres delete action"""
        return Database.Postgres.Delete(
            name=Ref.NutanixDB.Database(name="bekkam-pg-dnd")
        )
    ```
- Attributes supported for this class:
    1. database: Ref of the Postgres Instance


## Create Snapshot Task:

- User can use `Task.NutanixDB.PostgresDatabase.CreateSnapshot()` helper to create NDB Postgres Snapshot Action Task.
- Look [here](../../examples/Runbooks/NutanixDB_runbooks/postgresDB_create_snapshot.py) for example.

    ```
    Task.NutanixDB.PostgresDatabase.CreateSnapshot(
        name="postgres_create_snapshot",
        account=Ref.Account("era-account"),
        instance_config=postgresinstance_params(),
        outargs=output_variables(),
    )
    ```

### instance_config

- Use `instance_config` to provide database instance params required for Postgres Snapshot Action

- Use `Database.Postgres.CreateSnapshot()` in NDB models to create instance_config

    ```
    def postgresinstance_params():
        """Get the postgres instance config for postgres create snapshot action"""
        return Database.Postgres.CreateSnapshot(
            snapshot_name="snap-from-dsl",
            remove_schedule_in_days=2,
            # time_machine="@@{tm_uuid}@@",
            time_machine=Ref.NutanixDB.TimeMachine(name="dnd-nirbhay-pg_TM"),
            database=Ref.NutanixDB.Database(name="dnd-nirbhay-pg"),
        ),
    ```
- Attributes supported for this class:
    1. snapshot_name:           (String) Snapshot Name
    2. remove_schedule_in_days: (Integer) Removal Schedule
    3. time_machine:            (String) Time Machine Name
    4. database:                (String) Database Name

- Note: either of time_machine and database can be specified

### outargs

- Use `outargs` to provide output variable params required for Postgres Snapshot Action

- Use `PostgresDatabaseOutputVariables.CreateSnapshot()` in NDB models to create outargs

    ```
    def output_variables():
        """Get the defined output variable mapping for postgres create snapshot action"""
        return PostgresDatabaseOutputVariables.CreateSnapshot(
            platform_data='myplatformdata'
        )
    ```
- Attributes supported for this class:
    1. database_snapshot: Snapshot of the database
    2. properties: Properties of the entity, Eg -> Database instance, database, profiles
    3. dbserver_name: Name of the database server VM
    4. type: The type of the database created i.e., postgres_database
    5. dbserver_ip: IP address of the database server VM
    6. id: ID of database instance created
    7. parent_snapshot: Snapshot used to clone the database
    8. snapshot_uuid: Uuid of the Snapshot
    9. platform_data: Platform data is the aggregate data of all the output  variables supported

## Restore From Time Machine:

- User can use `Task.NutanixDB.PostgresDatabase.RestoreFromTimeMachine()` helper to create NDB Postgres Restore Action Task.
- Look [here](../../examples/Runbooks/NutanixDB_runbooks/postgresDB_restore_from_time_machine_with_point_in_time.py) for example using point in time to restore the database
- Look [here](../../examples/Runbooks/NutanixDB_runbooks/postgresDB_restore_from_time_machine_with_snapshot.py) for example using snapshot to restore the database

    ```
    Task.NutanixDB.PostgresDatabase.RestoreFromTimeMachine(
        name="postgres_restore_task_name",
        account=Ref.Account("ndb-account"),
        instance_config=postgresinstance_params(),
        outargs=output_variables(),
    )
    ```

### instance_config

- Use `instance_config` to provide database instance params required for Postgres Restore Action

- Use `Database.Postgres.RestoreFromTimeMachine()` in NDB models to create instance_config

    ```
    def postgresinstance_params():
        """Get the postgres instance config for postgres Restore From Time Machine action"""
        return Database.Postgres.RestoreFromTimeMachine(
            database=Ref.NutanixDB.Database("test-pg-inst"),
            snapshot_with_timeStamp=Ref.NutanixDB.Snapshot(
            "era_auto_snapshot (2023-03-01 14:46:17)"
            ),
            time_zone="America/Resolute",
            #point_in_time="2023-02-12 10:01:40",
        )
    ```
- Attributes supported for this class:
    1. database: Name of the Postgres Instance
    2. snapshot_with_timeStamp: Name of the snapshot along with TimeStamp (yyyy-mm-dd hh:mm:ss) Eg-> "era_auto_snapshot (2023-02-12 10:01:40)"
    3. point_in_time: point in Time to Restore yyyy-mm-dd hh:mm:ss Eg -> "2023-02-12 10:01:40"
    4. time_zone: Time Zone of the snapshot/point in time (If not given defaults to system timezone)

- Note: Either of snapshot_with_timeStamp and point_in_time can be specified

### outargs

- Use `outargs` to provide output variable params required for Postgres Restore Action

- Use `PostgresDatabaseOutputVariables.RestoreFromTimeMachine()` in NDB models to create outargs

    ```
    def output_variables():
        """Get the defined output variable mapping for postgres Restore From Time Machine action"""
        return PostgresDatabaseOutputVariables.RestoreFromTimeMachine(
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
    1. database_name: Name of the database instance
    2. database_instance_id: ID of database instance created
    3. tags: A tag is a label consisting of a user-defined name and a value that makes it easier to manage, search for, and filter entities
    4. properties: Properties of the entity, Eg -> Database instance, database, profiles
    5. time_machine: Time machine details when an instance is created
    6. time_machine_id: UUID of time machine
    7. metric: Stores storage info regarding size, allocatedSize, usedSize and unit of calculation that seems to have been fetched from PRISM
    8. type: The type of the database created i.e., postgres_database
    9. platform_data: Platform data is the aggregate data of all the output variables supported

## Clone Task:

- User can use `Task.NutanixDB.PostgresDatabase.Clone()` helper to create NDB Clone Action Task.
- Look [here](../../examples/Runbooks/NutanixDB_runbooks/postgresDb_clone_with_point_in_time.py) for example using point in time to clone the database
- Look [here](../../examples/Runbooks/NutanixDB_runbooks/postgresDb_clone_with_snapshot_id.py) for example using snapshot to clone the database
    ```
    Task.NutanixDB.PostgresDatabase.Clone(
        name="postgres_clone_task_name",
        account=Ref.Account("era"),
        database_server_config=database_server_params(),
        instance_config=instance_params(),
        timemachine_config=timemachine_params(),
        tag_config=tag_params(),
        outargs=output_variables(),
    )
    ```

### database_server_config

- Use `database_server_config` to provide database server params required for Postgres Clone Action

- Use `DatabaseServer.Postgres.Clone()` in NDB models to create database server config

    ```
    def database_server_params():
        """Get the Database server config for postgres clone action"""
        return DatabaseServer.Postgres.Clone(
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
    1. name: Name of the Postgres Instance
    2. password: Password of the database server
    3. cluster: Cluster to use for the database server
    4. compute_profile: Compute Profile to use for the database server
    5. network_profile: Netwrok Profile to use for the database server
    6. ssh_public_key:  RSA based public key to use for the database server
    7. description: Description of the database server


### instance_config

- Use `instance_config` to provide database instance params required for Postgres Clone Action

- Use `Database.Postgres.Clone()` in NDB models to create instance_config

    ```
    def instance_params():
        """Get the postgres instance config for postgres clone action runbook update"""
        return Database.Postgres.Clone(
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
    1. name: Name of the Postgres Instance
    2. description: Description of the Postgres Instance
    3. password: Password of the Postgres Instance
    4. database_parameter_profile: Database Parameter Profile to use for Postgres Instance
    5. pre_clone_cmd: Script to run before creating the Postgres Instance
    6. post_clone_cmd: Script to run after creating the Postgres Instance


### timemachine_config

- Use `timemachine_config` to provide time machine params required for Postgres Clone Action

- Use `TimeMachine.Postgres.Clone()` in NDB models to create timemachine_config

    ```
    def timemachine_params():
        """Get the Time Machine config for postgres clone action"""
        return TimeMachine.Postgres.Clone(
            time_machine_name=Ref.NutanixDB.TimeMachine("dnd-tm2"),
            point_in_time="2023-02-12 10:01:40",
            <!-- snapshot_with_timeStamp=Ref.NutanixDB.Snapshot(
            "era_auto_snapshot (2023-03-23 20:01:46)"
            ), -->
            time_zone="UTC",
        )
    ```
- Attributes supported for this class:
    1. time_machine: Name of the Time Machine
    2. snapshot_with_timeStamp: Name of the snapshot along with TimeStamp (yyyy-mm-dd hh:mm:ss) Eg-> "era_auto_snapshot (2023-02-12 10:01:40)"
    3. point in time: point in Time to Restore yyyy-mm-dd hh:mm:ss Eg -> "2023-02-12 10:01:40"
    4. time_zone: Time Zone of the snapshot/point in time (If not given defaults to system timezone)
    5. expiry_days: Number of days to expire
    6. expiry_date_timezone : Timezone to be used for expiry date
    7. delete_database: Boolean input for deletion of database
    8. refresh_in_days: Number of days to refresh
    9. refresh_time: Time at which refresh should trigger
    10. refresh_date_timezone: Timezone for the refresh time

- Note: Either of snapshot_with_timeStamp and point_in_time can be specified
### tag_config

- Use `tag_config` to provide tag params required for Postgres Clone Action

- Use `Tag.Clone()` in NDB models to create tag_config

    ```
    CloneTag = Ref.NutanixDB.Tag.Clone

    def tag_params():
        """Get the Tag config for postgres clone action"""
        return Tag.Clone(tags=[CloneTag("tag name", "")])
    ```
- Attributes supported for this class:
    1. clone: array of NDB Clone Tag Ref. Eg -> [ Ref.NutanixDB.Tag.Clone(name1, value1), Ref.NutanixDB.Tag.Clone(name=name2, value=value2) ]

### outargs

- Use `outargs` to provide output variable params required for Postgres Clone Action

- Use `PostgresDatabaseOutputVariables.Clone()` in NDB models to create outargs

    ```
    def output_variables():
        """Get the defined output variable mapping for postgres clone action"""
        return PostgresDatabaseOutputVariables.Clone()
    ```
- Attributes supported for this class:
    1. type: The type of the database created i.e., postgres_database
    2. id: ID of database instance created
    3. time_machine: Time machine details when an instance is created
    4. linked_databases: These are databases which are created as a part of the instance
    5. database_name: Name of the database instance
    6. database_nodes: Info of nodes of databases
    7. platform_data: Platform data is the aggregate data of all the output variables supported

