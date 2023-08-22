# Decompiling blueprints with DSL
Decompilation is a process to consume json data for any entity created in Calm and convert it back to DSL python helpers/classes. Summary of support for blueprint decompilation:
- Python helpers/classes are automatically generated with the use of jinja templates.
- Generated python file is formatted using [black](https://github.com/psf/black)
- Default values for most of the entities will be shown in decompiled file.
- Separate files are created under `scripts` directory in decompiled blueprint directory for storing scripts used in tasks, variables, guest customization (cloud init) etc.
- Provider VM specs (Other than AHV) / runtime editables for substrates  are stored in `specs` directory in blueprint directory.
- Name of created files in script/local directory are taken from the context of variable/task. For ex: Filename for service action task script: `Service_MySQLService_Action___create___Task_Task1`.
- NOTE: Blueprint action-runbook tasks decompilation is possible for only tree-type structure.<medium><i>(A node cann't have more than 1 parent)</i></medium>
    - Supported action-runbook:
        ```
            def DslParallelRunbook():
                "Runbook example for running tasks in parallel"

                Task.Exec.escript(name="root", script=code)
                with parallel() as p:

                    with branch(p):
                        Task.Exec.escript(name="Task1", script=code)

                    with branch(p):
                        Task.Exec.escript(name="Task2", script=code)
                        Task.Exec.escript(name="Task3", script=code)

                    with branch(p):
                        Task.Exec.escript(name="Task4", script=code)
                        Task.Exec.escript(name="Task5", script=code)
        ```
    
    - Unsupported action-runbook: (In below example `Task23` has more than 1 parent)
        ```
            def custom_action_2():

                Task.Exec.ssh(name="Task21", script="date")

                with parallel():
                    Task.Exec.ssh(name="Task22a", script="date")
                    Task.Exec.ssh(name="Task22b", script="date")

                Task.Exec.ssh(name="Task23", script="date")
        
        ```
## Decompilation of Blueprint with secrets:
DSL allows decompilation of bluerint with secrets(variable values on the server blueprint) using passphrase. Summary of decompilation: 
- For every secret, a file will be created in `.local` directory. Content of this file will be in encrypted form. User is not expected to change the content of file.
- A metadata file i.e. `decompiled_secrets.bin` will also be created in `.local` direcrory, that is used by dsl internally to identify the secret variables decompiled from the server, and check if the value if modified or not from the user.
- When user again tries to create the blueprint using passphrase used during decompilation, two cases may arrive:
    - If user has modified the content of file, it will not be decrypted at server and new variable will be created with new value (value = modifed-value) itself.
    - If user hasn't modified, value will be decrypted successfuly at server and create variable with original value.
- If user decompiles a blueprint with secrets and don't supply passphrase during creation, dsl throws a warning to let user know, he can also provide passphrase to create blueprint with secrets.

- Example:
    - Create a Blueprint `DecompiledExample` with two secret variables (`var1`, `var2`) at profile level.
    - Step-1: Decompile blueprint:
        ```
        >> calm decompile bp DecompiledExample --passphrase 12345
            [INFO] [calm.dsl.cli.bps:741] DecompiledExample found 
            [INFO] [calm.dsl.cli.bps:641] Decompiling blueprint DecompiledExample
            [2023-08-20 12:10:28] [WARNING] [calm.dsl.builtins.models.object_type:90] Additional Property (upgrade_runbook) found
            [INFO] [calm.dsl.decompile.decompile_render:37] Creating blueprint directory
            [INFO] [calm.dsl.decompile.decompile_render:39] Rendering blueprint file template
            [INFO] [calm.dsl.decompile.decompile_render:46] Formatting blueprint file using black
            [INFO] [calm.dsl.decompile.decompile_render:48] Creating blueprint file

            Successfully decompiled. Directory location: ~/projects/ideadevice-calm-dsl/DecompiledExample. Blueprint location: ~/projects/ideadevice-calm-dsl/DecompiledExample/blueprint.py

        ```
    
    - Step-2: Check the secret-files (profile variables) data at `.local` directory:
        ```
        >> cat ~/projects/ideadevice-calm-dsl/DecompiledExample/.local/Profile_HelloProfile_variable_var1                 
            7NmjNUHaG+VRfyzPNFhiWranONmDAvFMHoFLWp9YgAsTPR4fhyDFPL8xiA==:utf-8% 

        >> cat ~/projects/ideadevice-calm-dsl/DecompiledExample/.local/Profile_HelloProfile_variable_var2                
            eNC3k//fS+6agE6aEyX26ywgzTbWxdbmo9F3pxOvkus9Rv4XtM356ozLYg==:utf-8% 
        ```
    
    - Step 3: Modify the content of one of the variable
        ```
        >> echo "Changed value" > ~/projects/ideadevice-calm-dsl/DecompiledExample/.local/Profile_HelloProfile_variable_var1

        >> cat ~/projects/ideadevice-calm-dsl/DecompiledExample/.local/Profile_HelloProfile_variable_var1
            Changed value
        ```
    
    - Step 4: Add a new secret variable `var3` at profile in blueprint file.
        ```
        class HelloProfile(Profile):

            deployments = [HelloDeployment]

            var1 = CalmVariable.Simple.Secret(
                Profile_HelloProfile_variable_var1,
                label="",
                is_mandatory=False,
                is_hidden=False,
                runtime=True,
                description="",
            )

            var2 = CalmVariable.Simple.Secret(
                Profile_HelloProfile_variable_var2,
                label="",
                is_mandatory=False,
                is_hidden=False,
                runtime=True,
                description="",
            )

            var3 = CalmVariable.Simple.Secret(
                "new-variable-added-post-decompile",
                label="",
                is_mandatory=False,
                is_hidden=False,
                runtime=True,
                description="",
            )
        ```
    
    - Step 5: Create new blueprint with above file and diff passphrase. Bp creation will fail, as it was wrong passphrase
        ```
        >> calm create bp -f DecompiledExample/blueprint.py --passphrase 123 -n NewBlueprint

            [2023-08-20 12:30:48] [ERROR] [calm.dsl.api.connection:324] Oops! Something went wrong.
            {
                "error": {
                    "api_version": "3.1",
                    "code": 422,
                    "kind": "blueprint",
                    "message_list": [
                        {
                            "details": {},
                            "message": "Provided passphrase is wrong. Please enter correct passphrase",
                            "reason": "INVALID_REQUEST"
                        }
                    ],
                    "state": "ERROR"
                },
                "code": 422
            }
        ```
    
    - Step6: Create Blueprint with correct passphrase: This will create blueprint in following way:
        - Variable `var1` have been changed, so new value will be stored in it. This will also display warning at cli stating `variable value have been changed. Use debug log to check original value`
        - Variable `var2` have not been changed, so its original value (received from the server) will be stored. (Encrypted value will be decrypted successfully)
        - Variable `var3` is newly created. So it will be created with new value itself

        ```
         >> calm create bp -f DecompiledExample/blueprint.py --passphrase 123 -n NewBlueprint

            [WARNING] [calm.dsl.api.util:26] Value of decompiled secret variable var1 is modified
            [INFO] [calm.dsl.api.blueprint:306] Patching newly created/updated secrets
            [INFO] [calm.dsl.cli.bp_commands:251] Blueprint NewBlueprint created successfully.
        ```

## Decompilation of Blueprint without secrets:
- If user doesn't supplies the passphrase, it will create just empty files for all the secrets (i.e. variables, credentials) at the `.local` directory.
    ```
    calm decompile bp <BP_NAME>
    ```
- User can use `--with-secrets / -ws` to fill input the values of such secret variables during decompilation itself interactively
    ```
    calm decompile bp <BP_NAME> --with-secrets
    ```
- If user decompiles a blueprint without secrets and supplies passphrase during creation, dsl throws a warning to let user know, there is no need to pass passphrase.
- Flags:
    - User can use `-f/--file` to manually supply the json file location of blueprint to be decompiled.
    - User can use `-p/--prefix` to supply the prefix that will be added on the every entity original name.
    - User can use `-d/--dir` to supply the directory where decompiled-blueprint directory will be created.



