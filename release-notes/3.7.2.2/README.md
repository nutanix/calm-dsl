
# Major Feats

1. Added support for **project decompilation** [[see details](../../README.md#projects)], **environment decompilation** [[see details](../../README.md#environments)]

2. Added support to **create vm power actions** in blueprint. [see details](../../docs/Power-Actions-in-Blueprint/README.md)

3. Added support to create actions in `AhvUpdateConfigAttrs` class (Patch config actions).  [see details](../../docs/Blueprints/ahv_update_config/README.md)

4. Added support to **create vmware snapshot configs**. [see details](../../docs/Blueprints/snapshot_restore/README.md)

5. Added support for **downloadable images in simple bp model**. [see details](../../docs/Blueprints/downloadable_images/README.md)

6. [#252](https://github.com/nutanix/calm-dsl/issues/252) Added `calm unpublish marketplace` command to support unpublishing from all projects, specific projects, all versions of marketplace items.

7. [#264](https://github.com/nutanix/calm-dsl/issues/264) Added no expiration as an option for recurring jobs. [see details](../../docs/Job_scheduler/README.md)

# Bug Fixes
- [#291](https://github.com/nutanix/calm-dsl/issues/291) **Fixed decompilation of regex strings with backslashes** . Multiline type profile variable with a regex validation string including tokens such as \r, \n, \t will now get properly escaped during decompile.
- [#289](https://github.com/nutanix/calm-dsl/issues/289) Added support to **decompile UEFI boot_type in blueprint**
- [#283](https://github.com/nutanix/calm-dsl/issues/283) **Cluster macro decompile** issue fixed.
- [#273](https://github.com/ideadevice/calm-dsl/issues/273) Added support to **decompile blueprint with vm power actions.**
- [#144](https://github.com/nutanix/calm-dsl/issues/144) Updates version cache when config_file is supplied in cli options.

- [#213](https://github.com/nutanix/calm-dsl/issues/213) Fix static ip address decompilation assosciated with nics in the schema
- [#255](https://github.com/nutanix/calm-dsl/issues/255) Fixed `--with_endpoints` option when publishing a runbook to retain the endpoints as expected
- [#177](https://github.com/nutanix/calm-dsl/issues/177) Fixed endpoint targets decompile in blueprint tasks.
- Decompile issue fixed when package_element is of type CUSTOM and has call_runbook_tasks.
- Fixed decompile failure for while loop tasks.
- Added support to decompile, compile and create dynamic variables that use http task with basic auth.
- Added `-fc/--force` flag to create projects and environments.
- Fixes for [#192](https://github.com/nutanix/calm-dsl/issues/192), [#226](https://github.com/nutanix/calm-dsl/issues/226), [#150](https://github.com/nutanix/calm-dsl/issues/150), [#50](https://github.com/nutanix/calm-dsl/issues/50)
- Added support of `--all_projects` to command `calm update marketplace`
- Fixed calm get apps command to list apps with delete state.
- Fixed describe project command to list correct quotas assigned to a project.
- Added support which allows to publish bp/runbook to the marketplace attached with all projects and in approval pending state through `--all_projects/-ap` flag.
   
    &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; 
    `calm publish bp <bp_name> -v <version> --all_projects`
    
    
    &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;
    `calm publish runbook <runbook_name> -v <version> --all_projects`

- Added `--remove-project/rp` flag to remove projects while approving an MPI.

    &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; 
    `calm approve marketplace bp <bp_name> -v <version> --remove-project <project_name>`
    
    
    &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;
    `calm approve marketplace runbook <runbook_name> -v <version> --remove-project <project_name>` 

- Added option to choose multiple Nutanix accounts associated with the project, if present, while creating AHV provider spec.
- Added `nutanix_pc` as account type to list down nutanix accounts. e.g. `calm get accounts --type nutanix_pc`


