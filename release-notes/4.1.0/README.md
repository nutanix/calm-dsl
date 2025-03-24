
# Improvements

- <b>Support for external file in Runbook Input variables for execution:</b> Added support to read variable values from an external file for runtime editable variables and supply them using `runtime_params_file` param in case of runbook job executable object. For more details read <b>Execute Runbook</b> section [here](https://www.nutanix.dev/docs/self-service-dsl/models/SchedulerJob/).

- <b>Support to decompile without black formatting:</b> Added `--no-format/-nf` flag in all decompilable entities. This will allow to decompile without python black formatting and resolve [#212](https://github.com/nutanix/calm-dsl/issues/212). You can later modify blueprint according to usecase and optionally format it using `black <file-path>`.

- [#315](https://github.com/nutanix/calm-dsl/issues/315), [#316](https://github.com/nutanix/calm-dsl/issues/316) <b>Allowing to specify JSON output format for calm get runbooks command:</b> Added `-o/--out` flag in `calm get runbooks` command. 



# Bug Fixes

- Fix the issue preventing addition of empty values for memory, vCPU, and numSocket in AHV patch configs. From this release onwards when modifying, adding, or deleting disks or NICs, there is no mandate to provide values for memory, vCPU, or numsocket.

- Fixed accidental deletion of system applications in `calm delete app` command by adding `--all-items/-a` flag. If this flag is True it will delete system apps too, else it will only delete apps that are specified.

- [#221](https://github.com/nutanix/calm-dsl/issues/221) Fixed missing descriptions in Blueprints created by inheriting from the VmBlueprint class.

- [#306](https://github.com/nutanix/calm-dsl/issues/306) Fixed name of switch `existing_marketplace_bp` in `calm publish bp` command

