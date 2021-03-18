# Environment Changes

## CLI commands

- `calm launch bp --environment “<environment name>”`: The blueprint will be patched with the given environment to create a new blueprint and the application will be launched with the patched Blueprint.

- `calm launch marketplace bp --environment “<environment name>”`: The MP blueprint will be patched with the given environment to create a new blueprint and the application will be launched with the patched Blueprint.

- `calm launch marketplace item --environment “<environment name>”`: The MPI will be patched with the given environment to create a new blueprint and the application will be launched with the patched Blueprint.

- `calm get brownfield vms -p <project> -a <account_name>`: Added account cli option, that user should provide if there are multiple accounts in the given project.

- `calm get environments -p <project>`: Added command for listing out environments.

- `calm delete environment <environment_name> -p <project>`: It will delete environment attached to given project


## Builtin-Models

### Profile Model

Added `environments` attribute is added which specify the environment used for the given profile. If not supplied, profile will be created with `All Project Accounts` 

```
class DefaultProfile(Profile):

    deployments = [MySQLDeployment]
    environments = [Ref.Environment(name=ENV_NAME)]

    @action
    def test_profile_action():
        exec_ssh(name="Task5", script='echo "Hello"', target=ref(MySQLService))
```

### Substrate Model

Added account attribute at substrate level. Users can select account from multiple accounts whitelisted in the project. If account is not provided, it will:
- select account from environment if environment is given at profile level
- select any account from the project if the environment is not given.

```
class AhvSubstrate(Substrate):
    """AhvSubstrate configuration"""

    provider_spec = AhvVm
    account = Ref.Account(name=account_name)
```

### VmProfile Model

Added `environments` attribute is added which specify the environment used for the given profile. If not supplied, profile will be created with `All Project Accounts` 

```
class AhvVmSmalProfile(VmProfile):
    """VmProfile configuration"""

    provider_spec = AhvVm
    environments = [Ref.Environment(name=ENV_NAME)]
```

### SimpleBlueprint Model

Added `environments` attribute is added which specify the environment used for the given profile. If not supplied, profile will be created with `All Project Accounts` 

```
class SampleSimpleBlueprint(SimpleBlueprint):
    """SimpleBlueprint configuration"""

    deployments = [MySqlDeployment]
    environments = [Ref.Environment(name=ENV_NAME)]
```

### Environment Model

Added `providers` attribute that will attach infra to the environment. Providers attribute is the same as the project model has.

NOTE: All the infra included in the environment, will automatically be added to the project by which environment is attached.
 
For any provider-account, user can attach two substrate configurations each for Linux and Windows os.

```
class ProjEnvironment(Environment):
    """Project Environment configuration"""

    substrate = [MySqlSubstrate]
    providers = [
        Provider.Ntnx(
            account=Ref.Account(NTNX_ACCOUNT_2_NAME),
            subnets=[
                Ref.Subnet(
                    name=NTNX_ACCOUNT_2_SUBNET_1,
                    cluster=NTNX_ACCOUNT_2_SUBNET_1_CLUSTER,
                )
            ],
        ),
        Provider.Gcp(account=Ref.Account(GCP_ACCOUNT_NAME)),
    ]
```

### Project Model

Added `default_environment` that will be the reference to default environment in the project

Functionality-wise changes:
- Users can add multiple environments in the project.
- User can provide multiple accounts for any given provider type
- By default, the environment supplied at 0th index will be considered as default.

```
class SampleProject(Project):
    """Project Environment configuration"""

    substrate = [MySqlSubstrate]
    providers = [
        Provider.Ntnx(
            account=Ref.Account(NTNX_ACCOUNT_2_NAME),
            subnets=[
                Ref.Subnet(
                    name=NTNX_ACCOUNT_2_SUBNET_1,
                    cluster=NTNX_ACCOUNT_2_SUBNET_1_CLUSTER,
                )
            ],
        ),
        Provider.Gcp(account=Ref.Account(GCP_ACCOUNT_NAME)),
    ],
    envs = [ProjEnvironment1, ProjEnvironment2]
    default_environment = ref(ProjEnvironment1)
```

# Runbook Changes

## CLI commands

- `calm describe marketplace item`: It will print the summary of marketplace items (blueprint/runbook).

- `calm get marketplace items`: It will list available marketplace items (blueprint/runbook).

- `calm run marketplace item`: It will execute marketplace item of type runbook.

- `calm unpublish marketplace item`: It will unpublish marketplace item (blueprint/runbook).

- `calm get marketplace runbooks`: It will list available marketplace manager runbooks.

- `calm describe marketplace runbook`: It will print the summary of marketplace manager runbook.

- `calm approve marketplace runbook`: It will approve marketplace manager runbook.

- `calm publish marketplace runbook`: It will publish marketplace manager runbook to marketplace store.

- `calm update marketplace runbook`: It will update marketplace manager runbook.

- `calm delete marketplace runbook`: It will delete marketplace manager runbook.

- `calm reject marketplace runbook`: It will reject marketplace manager runbook.

- `calm publish runbook`: It will publish runbook to marketplace manager.

- `calm run marketplace runbook`: It will execute marketplace manager runbook.

## Builtin-Models

### Endpoint Model

Create a Endpoint using the `CalmEndpoint` model. This model supports creation of Linux, Windows, HTTP endpoint types, whereas Linux, Windows endpoint supports IP, VM endpoint. Following are the examples of creating different styles of endpoint:

Example 1: Creating a Linux VM Endpoint of Static Filter type
```
LinuxCred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="endpoint_cred")

vm_endpoint = Endpoint.Linux.vm(
    vms=[Ref.Vm(uuid="85a5a955-9cd6-4d48-a965-411e69127242")],
    cred=LinuxCred,
    account=Ref.Account("NTNX_LOCAL_AZ"),
)
```

Example 2: Creating a Linux VM Endpoint of Dynamic Filter type
```
linux_ahv_dynamic_vm_endpoint1 = Endpoint.Linux.vm(
    filter="name==vm_name1",
    cred=LinuxCred,
    account=Ref.Account("NTNX_LOCAL_AZ"),
)
```