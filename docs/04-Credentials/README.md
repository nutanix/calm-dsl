# Calm allows managing the following types of credentials:

## Static Credentials

Static credentials in Calm are modelled to store secrets (password or SSH private key) in the credential objects that are contained in the blueprints that the applications copy.

### Built-in Helpers

- User can use `basic_cred()` helper to define static credentials.

    ```
    Centos = basic_cred(
                username = "cred_username",
                password = "cred_password",
                name = "cred_name",
                type = "PASSWORD",
                default=True
            )

    ```

- Use `type = PASSWORD/KEY` for defining in password/ssh key form.
- Use `default=True` for defining default cred in case of multiple creds
- Use `editables={}` to define editable attribute at runtime.


## Dynamic Credentials
- Calm supports external credential store integration for dynamic credentials. A credential store holds username and password or key certificate combinations and enables applications to retrieve and use credentials for authentication to external services whenever required

###  Built-in Helpers

- User can use `dynamic_cred()` helper for defining dynamic creds.
    ```
    DefaultCred = dynamic_cred(
                username = "cred_username",
                account = Ref.Account(name=CRED_PROVIDER),
                variable_dict={"path": SECRET_PATH},
                name="default cred",
                type="PASSWORD"
                default=True,
            )
    ```

- Use `account = Ref.Account(name="cred_provider_account")` provider account for the credential.
- Use `type = PASSWORD/KEY` for defining in password/ssh key form.
- Use `default=True` for defining default cred in case of multiple creds
- Use `editables={}` to define editable attribute at runtime.
