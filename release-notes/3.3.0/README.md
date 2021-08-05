# Brownfield Application

## CLI commands

- `calm get brownfield vms -p <project> -a <account_name>`: Added account cli option, that user should provide if there are multiple accounts in the given project.

- `calm launch bp <bp_name> -b <brownfield_deployments_file_location> -n <app_name>`. Command will launch existing blueprint using brownfield deployments to create brownfield application. Sample file look [here](examples/Brownfield/separate_file_example/brownfield_deployments.py).
