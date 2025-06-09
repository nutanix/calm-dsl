
# Improvements

- <b>Adding support for DSL to be used with NCM Self Service decoupled from PC (NCM 1.5):</b> DSL can now be used for both Self Service on-prem (opt-out) and Self-Service as decoupled NCM (opt-in). Initialising DSL will require users to pass the correct Prism Central host URL depending on the deployment type:

    - For Self-Service on PC or Self-Service VM: use the Prism Central Host IP/hostname and port.
    - For Self-Service on decoupled NCM: use Prism Central FQDN as hostname and port.

    It can also be passed with the `-i/--ip` flag with the CLI commands `calm init dsl` or `calm set config`.

- <b>Post the NCM application deployment (Self Service running in decoupled NCM) will have the following changes:</b>
    - Marketplace related operations will be limited to Self Service Domain. For instance, `calm get marketplace items` will only list MPI's present in Self Service excluding preferred partner apps listed in Admin Centre Marketplace.
    - Similary, application related operations will be limited to Self Service Domain. For instance, `calm get apps` will only list applications deployed via Self-Service blueprints and listed in the `Applications` page in Self-Service app.
    - Tunnels on a VPC go into the disconnected mode due to change in the NCM cluster external IP address. Use the calm reset DSL command to spin up a new tunnel VM and delete the old tunnel VM. For more information, see [DSL CLI Commands](https://www.nutanix.dev/docs/self-service-dsl/getting-started/commands/)