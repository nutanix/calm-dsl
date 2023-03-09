# Improvment and Bug Fixes:

- Fixes #230. Fetch all users for dsl update cache.
- Added decompile support for Dynamic creds in blueprint. Jira: CALM-34123
- Fixes #225. Delete temp blueprint in command `calm create app -n app_name` if app name already exists
- Fixes a issue where decompile is not working for http task when requested payload for POST/PUT call is empty. Jira: CALM-34513
- Fixes #190. Make retries_enabled, connection_timeout, read_timeout as configurable parameter.
- Fixes #231. Expose dynamic_cred helper through calm.dsl.runbooks.
- Fixes #251. Added command to manual sync platform account.
- Fixes #204. Added `--apend-only` flag to only append data for project updation.
- Fixes #237. Fixes the env variables ignorance for config data.
- Fixes a issue where project updation was failing with `Account not found`. Jira: CALM-3335


# Built-in Model Changes

- Added support for passing macro value for cluster field in Ahv Vm Configuration.
```
class MyAhvVM(AhvVm):

    resources = MyAhvVmResources
    categories = {"AppFamily": "Demo", "AppType": "Default"}
    cluster = Ref.Cluster("@@{cluster_variable.uuid}@@")
```

# Command changes:

- Added command to manual sync provider account.
```
calm sync account <account_name>
```

- Added an additional flag (`--append-only`) to  update project command which will append the `users, groups, accounts, subnets, vpcs` mentioned without affecting any of the existing and also the environment will remain unchanged.
```
calm update project <project_name> --file <project_file> --append-only
```

- Added parameter to set config enable/disable retries and supply the connection_timeout, read_timeout for server calls.
```
# To enable/disable retries
>> calm set config < --retries-enabled / -re > / < --retries-disabled / -rd >

# TO set connection timeout
>> calm set config --connection-timeout/-ct <INTEGER>

# To set read timeout
>> calm set config --read-timeout/-rt <INTEGER>

# To show current config
>> calm show config
```