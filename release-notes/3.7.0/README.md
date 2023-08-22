# Major Feats

## Approval Policy
Calm-Dsl 3.7.0 has started supporting approval policy operations. [Read more here](../../docs/Approvals)

## Accounts
Calm-DSL 3.7.0 supports create, update, delete operations on private and public accounts in Calm. [Read more here](../../docs/Accounts) 

## Decompile Runbooks
Calm-DSL 3.7.0 supports decompile of Runbooks without secrets. [Read more here](../../docs/Decompiling%20Runbooks)

## Decompiling Blueprint with secrets
Calm-DSL 3.7.0 supports decompile of Bluepriny with secrets. [Read more here](../../docs/Decompiling%20Blueprints/)

## NDB-Integrartion
Calm-DSL 3.7.0 supports create, update, delete operations for Postgres Database thorugh NDB Task in Runbook. [Read more here](../../docs/NDB-Intergration/) 

# Improvment and Bug Fixes:

- [#265](https://github.com/nutanix/calm-dsl/issues/265). **Project field is made optional**  when initializing Calm-DSL for the first time.
- [#178](https://github.com/nutanix/calm-dsl/issues/178). **Decompilation of Blueprint with accounts and environment**: During blueprint decompile, account information at substrate level will be provided along with environment information at profile level. .
- [#250](https://github.com/nutanix/calm-dsl/issues/250). Resolved cluster decompilation if cluster name has hypen or special character.
- [#266](https://github.com/nutanix/calm-dsl/issues/266). **Enable/Disable Quota in Projects**.
    - During project creation, it checks if quotas are avaialble in project payload (json or python file). If it is there, then quotas are enabled in the project.
    - During project updation, there can be three cases:
        - If the project already has quotas set and enabled and quotas are present in {project_file} then the quotas would be updated
        - If the project already has quotas set and enabled and there are no quotas in {project_file} then the original quotas would be left as it is.
        - If the project did not have quotas enabled/set and the {project_file} has quotas then the quotas would be enabled and set.
    - As part of this fix, two new cli switches have been added ( i.e. `--enable-quotas` and `--disable-quotas`) to the project update command.
- [#268](https://github.com/nutanix/calm-dsl/issues/268). Resolved issue with parallel tasks decompilation.
- Adding resource-type as editable for dynamic creds. For more discussion check [here](https://nutanix.slack.com/archives/GHGEAFZ3K/p1683317518387739)
- Fixed the issue with Update cache (error: 'AhvClustersCacheDoesNotExist') if cluster name has a hyphen. (CALM-38702).
