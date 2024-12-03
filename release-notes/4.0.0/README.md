
# Major Feats

1. <b>Cloud Provider Framework in Self-Service:</b> Added support to configure cloud providers to provision and manage any workloads on the supported private and public cloud. The configuration involves defining the schema, resource types, actions, and so on. You can then consume the configured cloud provider in a runbook task. For more details go through following pages:
   - [Getting started on Providers](https://www.nutanix.dev/docs/self-service-dsl/getting-started/providers/)
   - [Understanding Provider model in DSL](https://www.nutanix.dev/docs/self-service-dsl/models/Provider/)
   - [Resource Type model in DSL](https://www.nutanix.dev/docs/self-service-dsl/models/ResourceType/)
   - [Provider Task model in DSL](https://www.nutanix.dev/docs/self-service-dsl/models/Task/providertask/)

# Improvements

- <b>Error Handling in Runbooks and Blueprints:</b> Added `status_map_list` param at Task level which will enable to continue with the execution of the runbook or blueprint workflow on task failure, instead of failing the entire workflow based on an individual task status. The failed tasks are marked with a Warning status to proceed to the subsequent task in the workflow. For more details read [here](https://www.nutanix.dev/docs/self-service-dsl/models/Task/runbooktask/#error-handling-in-runbooktask) 

- <b>Output Variables at the Runbook Level:</b> Added support to add output variables at the Runbook level so that the task variables that is set as output in individual tasks (such as HTTP, Set Variable and so on) are
available for viewing and for external consumption. For more details read [here](https://www.nutanix.dev/docs/self-service-dsl/getting-started/runbooks/#output-variables-in-runbook)

- <b>Clone a runbook:</b> Added `calm clone runbook` commmand to clone a runbook in Self-Service. For more details go through `Cloning Runbook` section [here](https://www.nutanix.dev/docs/self-service-dsl/getting-started/runbooks/#cloning-runbook)

- <b>Publish Blueprint to the Marketplace Without Platform-Dependent Configuration:</b> Added `--without-platform-data/-wp` flag in `calm publish bp` command to clear all the platform-dependent fields in Blueprint VM configuration before publishing the blueprint to the marketplace. Clearing the platform-dependent fields allows Self-Service to populate VM configuration fields from the VM configurations of the environment you select during the launch of the Marketplace blueprint. For more details read about publishing without platform dependent fields [here](https://www.nutanix.dev/docs/self-service-dsl/getting-started/marketplace_item/#publishing-blueprint-to-marketplace-manager-without-platform-dependent-fields)

- <b>`status_mapping` param used for response code mapping in the HTTP Task will be deprecated</b>: Use `response_code_status_map` param for mapping HTTP response codes to task statuses. For more details read how to use `response_code_status_map` in [CalmTask](https://www.nutanix.dev/docs/self-service-dsl/models/Task/calmtask/#response-code-range-mapping-in-http-calmtask) and [RunbookTask](https://www.nutanix.dev/docs/self-service-dsl/models/Task/runbooktask/#response-code-range-mapping-in-http-runbooktask).

- Removed use of centos disk image from blueprint generated from `calm init bp` command. From now on, an empty placeholder will be generated in blueprint. Fill valid disk image according to your usecase. For more details read [here](https://www.nutanix.dev/docs/self-service-dsl/tutorial/rocky_image_in_blueprint/)

- Updated `calm describe app` command to display more details about applications of AHV, VMware, AWS, Azure, GCP providers.

- [#229](https://github.com/nutanix/calm-dsl/issues/229) Added `windev` command in DSL Makefile. Use `make windev` to build DSL on Windows machine.

# Bug Fixes

- Block blueprint launch if blueprint has snapshot configs but no protection policy data when user passes `--ignore_runtime_variables/-i` flag

- Fix missing hyphen(-) in endpoint name while decompiling a bluperint or runbook.

