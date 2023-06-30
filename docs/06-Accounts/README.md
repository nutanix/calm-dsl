# Calm allows CRUD of accounts:

## <u>DSL Commands</u>
</br>

### 1. Create Account Command

Allows creating account from account dsl file.

`calm create account --file="FILEPATH"`

#### Flags:

- `--name` to give account name
- `--force` deletes existing account with the same name before create
- `--auto-verify` verifies the account after successfull account creation

</br>

### 2. Compile Account Command

Allows compiling account from account dsl file.

`calm compile account --file="FILEPATH"`

#### Flags:

- `--out` to give output format

</br>

### 3. Update Account Command

Allows updating account from account dsl file.

`calm update account --file="FILEPATH" --name="ACCOUNT_NAME"`

#### Flags:

- `--updated-name` to give name to the updated account

</br>

### 4. Delete Account Command

Allows deleting an account.

`calm delete account ACCOUNT_NAME`

</br>

### 5. Sync Account Command

Allows syncing a platform an account.

`calm sync account ACCOUNT_NAME`

</br>

### 6. Verify Account Command

Allows verifying an account.

`calm verify account ACCOUNT_NAME`

</br>

### 7. Describe Account Command

Describes an account.

`calm describe account ACCOUNT_NAME`

</br>

## <u>Account Models</u>

</br>

### AHV Account Model

- User can use `AccountResources.Ntnx()` helper to define the resources for AHV account.

    ```
    from calm.dsl.builtins import Account, AccountResources
    from calm.dsl.constants import ACCOUNT

    class example_ahv_account(Account):

        type = ACCOUNT.TYPE.AHV
        sync_interval = SYNC_INTERVAL_SECS
        resources = AccountResources.Ntnx(
            username=USERNAME, password=PASSWORD, server=SERVER, port=PORT
    )
    ```

- Use `type = ACCOUNT.TYPE.AHV` for defining the provider as AHV.
- Use `username` for defining the authentication username.
- Use `password` to define the authentication password.
- Use `server` for defining PC IP.
- Use `port` to define PC port.

</br>

### AWS Account Model

- User can use `AccountResources.Aws()` helper to define the resources for AWS account.

    ```
    from calm.dsl.builtins import Account, AccountResources
    from calm.dsl.constants import ACCOUNT

    class example_aws_account(Account):

        type = ACCOUNT.TYPE.AWS
        resources = AccountResources.Aws(
            access_key_id=ACCESS_KEY_ID,
            secret_access_key=SECRET_ACCESS_KEY,
            regions=[
                {
                    "name": "eu-central-1"
                    "images": [
                        "IMAGE_NAME_1",
                        "IMAGE_NAME_2",
                    ]
                },
                {
                    "name": "ap-south-1"
                }
            ],
        )
    ```

- Use `type = ACCOUNT.TYPE.AWS` for defining the provider as AWS.
- Use `access_key_id` for defining the access key id.
- Use `secret_access_key` to define the secret access key.
- Use `regions` to define regions and public images for the regions.

</br>

### AWS C2S Account Model

- User can use `AccountResources.Aws_C2s()` helper to define the resources for AWS C2S account.

    ```
    from calm.dsl.builtins import Account, AccountResources
    from calm.dsl.constants import ACCOUNT

    class example_aws_c2s_account(Account):

        type = ACCOUNT.TYPE.AWS_C2S
        resources = AccountResources.Aws_C2s(
            account_address=C2S_ACCOUNT_ADDRESS,
            client_certificate=CLIENT_CERTIFICATE,
            client_key=CLIENT_KEY,
            role=ROLE,
            mission=MISSION,
            agency=AGENCY,
            regions=[
                {
                    "name": "eu-central-1"
                    "images": [
                        "IMAGE_NAME_1",
                        "IMAGE_NAME_2",
                    ]
                },
                {
                    "name": "ap-south-1"
                }
            ],
        )
    ```

- Use `type = ACCOUNT.TYPE.AWS_C2S` for defining the provider as AWS C2S.
- Use `account_address` for defining C2S account address.
- Use `client_certificate` for defining client certificate.
- Use `client_key` to define client key.
- Use `role` to define role.
- Use `mission` to define mission.
- Use `agency` to define agency.
- Use `regions` to define regions and public images for the regions.

</br>

### Azure Account Model

- User can use `AccountResources.Azure()` helper to define the resources for Azure account.

    ```
    from calm.dsl.builtins import Account, AccountResources
    from calm.dsl.constants import ACCOUNT

    class example_azure_account(Account):

        type = ACCOUNT.TYPE.AZURE
        sync_interval = 3900
        resources = AccountResources.Azure(
            tenant_id=TENANT_ID,
            client_id=CLIENT_ID,
            client_key=CLIENT_KEY,
            cloud="PublicCloud",
        )
    ```

- Use `type = ACCOUNT.TYPE.AZURE` for defining the provider as Azure.
- Use `tenant_id` for defining directory/tenant id.
- Use `client_id` for defining application/client id.
- Use `client_key` to define client key/secret.
- Use `cloud` to define cloud environment.

</br>

### GCP Account Model

- User can use `AccountResources.Gcp()` helper to define the resources for GCP account.

    ```
    from calm.dsl.builtins import Account, AccountResources
    from calm.dsl.constants import ACCOUNT

    class example_gcp_account(Account):

        type = ACCOUNT.TYPE.GCP
        resources = AccountResources.Gcp(
            project_id=PROJECT_ID,
            private_key_id=PRIVATE_KEY_ID,
            private_key=PRIVATE_KEY,
            client_email=CLIENT_EMAIL,
            token_uri=TOKEN_URI,
            client_id=CLIENT_ID,
            auth_uri=AUTH_URI,
            auth_provider_cert_url=AUTH_PROVIDER_x509_CERT_URL,
            client_cert_url=CLIENT_x509_CERT_URL,
            regions=["eu-central-1"],
            public_images=[PUBLIC_IMAGE_1, PUBLIC_IMAGE_2],
            gke_config={"server": SERVER_IP, "port": PORT},
        )
    ```

- Use `type = ACCOUNT.TYPE.GCP` for defining the provider as GCP.
- Use `project_id` for defining project id.
- Use `private_key_id` for defining private key id.
- Use `private_key` to define private key.
- Use `client_email` to define client email.
- Use `token_uri` to define token uri.
- Use `client_id` to define client id.
- Use `auth_uri` to define authentication uri.
- Use `auth_provider_cert_url` to define authentication provider certificate url.
- Use `client_cert_url` to define client certificate url.
- Use `regions` to define regions.
- Use `public_images` to define public images.
- Use `gke_config` to define gke configuration.

</br>

### VMware Account Model

- User can use `AccountResources.Vmware()` helper to define the resources for VMware account.

    ```
    from calm.dsl.builtins import Account, AccountResources
    from calm.dsl.constants import ACCOUNT

    class example_vmware_account(Account):

        type = ACCOUNT.TYPE.VMWARE
        sync_interval = SYNC_INTERVAL_SECS
        resources = AccountResources.Vmware(
            username=USERNAME,
            password=PASSWORD,
            server=SERVER,
            port=PORT,
            price_items={"vcpu": 0.02, "memory": 0.01, "storage": 0.0003},
        )
    ```

- Use `type = ACCOUNT.TYPE.VMWARE` for defining the provider as Vmware.
- Use `username` for defining username.
- Use `password` for defining password.
- Use `server` to define server ip.
- Use `port` to define port.
- Use `price_items` to define resource usage costs.

</br>

### Kubernetes Account Model

- User can use `AccountResources.K8s_Vanilla` helper to define the resources for Kubernetes Vanilla type.

    ```
    from calm.dsl.builtins import Account, AccountResources, AccountAuth
    from calm.dsl.constants import ACCOUNT

    class test_k8s_vailla_account_123321(Account):
        """This is a test account"""

        type = ACCOUNT.TYPE.K8S_VANILLA
        resources = AccountResources.K8s_Vanilla(
            auth=AccountAuth.K8s.basic(username=USERNAME, password=PASSWORD),
            server=SERVER,
            port=PORT,
        )
    ```

- Use `type = ACCOUNT.TYPE.K8S_VANILLA` for defining the provider as Kubernetes of type Vanilla.
- Use `server` to define server ip.
- Use `port` to define port.
- Use `auth` for defining authentication object.
    - <u>Basic Auth</u>:
        ```
        auth=AccountAuth.K8s.basic(
            username=USERNAME, 
            password=PASSWORD
        )
        ```
        - Use `username` for defining username.
        - Use `password` for defining password.

    - <u>Client Certificate as Auth Type</u>:
        ```
        auth=AccountAuth.K8s.client_certificate(
            client_certificate=CERTIFICATE,
            client_key=KEY,
        )
        ```
        - Use `client_certificate` for defining client certificate.
        - Use `client_key` for defining client key.

    - <u>CA Certificate as Auth Type</u>:
        ```
        auth=AccountAuth.K8s.ca_certificate(
            ca_certificate=CA_CERTIFICATE,
            client_certificate=CERTIFICATE,
            client_key=KEY,
        )
        ```
        - Use `ca_certificate` for defining ca certificate.
        Use `client_certificate` for defining client certificate.
        - Use `client_key` for defining client key.

    - <u>Service Account as Auth Type</u>:
        ```
        auth=AccountAuth.K8s.service_account(
            ca_certificate=CA_CERTIFICATE,
            token=TOKEN,
        )
        ```
        - Use `ca_certificate` for defining ca certificate.
        - Use `token` for defining token.

</br>

### NDB Account Model

- User can use `AccountResources.NDBProvider()` helper to define the resources for NDB account.

    ```
    from calm.dsl.builtins import Account, AccountResources, Ref
    from calm.dsl.constants import ACCOUNT

    class example_ndb_provider_account(Account):

        type = ACCOUNT.TYPE.NDB
        resources = AccountResources.NDBProvider(
            parent=Ref.Account("AHV_ACCOUNT_NAME"),
            variable_dict={
                "server_ip": "ENDPOINT_VALUE",
                "username": "USERNAME_VALUE",
                "password": "PASSWORD_VALUE",
            },
        )
    ```

- Use `type = ACCOUNT.TYPE.NDB` for defining the provider as NDB.
- Use `parent=Ref.Account("AHV_ACCOUNT_NAME")` for defining the parent(should be of type 'AHV').
- Use `variable_dict` for defining server ip, username and password.

</br>

### Credential Provider Model

- User can use `AccountResources.CredentialProvider()` helper to define the resources for Credential Provider.

    ```
    from calm.dsl.runbooks import RunbookTask as Task
    from calm.dsl.constants import ACCOUNT
    from calm.dsl.builtins import (
        Account,
        CalmVariable,
        action,
        CredAccountResources,
        AccountResources,
    )

    class HashiCorpResources(CredAccountResources):

        variables = [
            CalmVariable.Simple.string(name=VAR_NAME, value=VAR_VALUE),
            CalmVariable.Simple.Secret.string(name=SEC_VAR_NAME, value=SEC_VAR_VALUE),
        ]

        cred_attrs = [
            CalmVariable.Simple.string(name=VAR_NAME_2, value=VAR_VALUE_2),
            CalmVariable.Simple.Secret.string(name=SEC_VAR_NAME_2, value=SEC_VAR_VALUE_2),
        ]

        @action
        def DslSetVariableRunbook():
            "Runbook example with Set Variable Tasks"

            Task.Exec.escript(name="Task1", script="print '@@{var1}@@ @@{var2}@@'")
            Task.Exec.escript(name="Task2", script="print '@@{var1}@@ @@{var2}@@'")


    class HashiCorpVault_Cred_Provider(Account):
        """This is a test credential provider"""

        type = ACCOUNT.TYPE.CREDENTIAL_PROVIDER
        resources = AccountResources.CredentialProvider(
            vault_uri="VAULT_URI_VALUE",
            vault_token="VAULT_TOKEN_VALUE",
            resource_config=HashiCorpResources,
        )
    ```

- Use `type = ACCOUNT.TYPE.CREDENTIAL_PROVIDER` for defining type as Credential Provider.
- Use `vault_uri` for defining vault uri.
- Use `vault_token` for defining vault token.
- Use  `resource_config` for defining resources.
    - `variables` for defining variables.
    - `cred_attrs` for defining credential attributes.
    - Describe runbook under `@action`

