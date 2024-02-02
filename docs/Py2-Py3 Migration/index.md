## Updating eScript Tasks and Variables of Python 2 to Python 3 Using Self-Service DSL

This article provides the necessary steps to update eScripts in the tasks of your deployed applications from Python 2 to Python 3.

### Limitations

- For multi-VM applications, use the following Self-Service DSL steps to update application scripts to Python 3.

- For single-VM applications, use the app edit to update application scripts to Python 3.

### Important Points :
• Single-VM applications with custom actions having dynamic variables with secrets can be updated using Self-Service DSL only.<br>
• Snapshot config tasks or variables can be updated using Self-Service DSL only.<br>
• Patch-config action updates are not currently supported in both Single-VM and Multi-VM applications. As a workaround, you can soft delete and brownfield import applications.<br>

### Procedure

1. Describe the application that needs to be modified. For example:
```
calm describe app-migratable-entities <app_name>
```
Where `<app_name>` is the name of the deployed application in which you can update the script from Python 2 to Python 3.

2. Decompile the application blueprint. For example:
```
calm decompile app-migratable-bp <app_name> --dir <dir_name>
```
Where `<dir_name>` is an optional argument for the directory name in which you want to decompile the application blueprint.

3. Edit the blueprint to update the task to use Python 3 scripts.

4. Update the application.
```
calm update app-migratable-bp <app_name> -f <blueprint_file_location_path>
```
Where `<blueprint_file_location_path>` is the location of the decompiled blueprint file (the blueprint file in which you updated tasks to use Python 3 scripts).

### Example 

#### Update Custom Action Scripts of a Deployed Multi-VM Application

Suppose you have a deployed Multi-VM app with a custom action with the following details:

• Application name: azure-postgres-server<br>
• Custom action name: CustomAction1<br>
• An Execute task of type Python 2 eScript within the custom action:
``` 
#py2
text = "Sample Runbook with Escript Task"
encoded_text = base64.b64encode(text)
print "encoded string is: ", encoded_text
```

To update this script in the custom action to Python 3 using Self-Service DSL, do the following:

1. Use the following command to display the eScript tasks or variables that you can migrate:
    ```
    $ calm describe app-migratable-entities azure-postgres-server
    ```

    Where `azure-postgres-server` is the application name.

2. Create a directory and decompile the application blueprint using the following command:
    ```
    $ calm decompile app-migratable-bp azure-postgres- server --dir appeditescript
    ```
    Where `appeditescript` is the directory in which the application blueprint is decompiled. The decompiled blueprint only contains eScript tasks and variables.

3. Navigate to your working directory:
     ```
     $ cd appeditescript/
     ```
 
4. To update the function reference, open the file and update the reference from `CalmTask.Exec.escript.py2` to `CalmTask.Exec.escript.py3`.
    ```
    CalmTask.Exec.escript.py3(
        name="B64 usage task",
        filename=os.path.join("scripts", "Profile_Default_Action_CustomAction1_Task_B64usagetask.py"),
        target=ref(Service1)
    )
    ```

5. Navigate to the scripts file:
    ```
    $ cd scripts/
    ```
6. Open the file `Profile_Default_Action_CustomAction1_Task_B64usagetask.py` to update the existing Python 2 script to Python 3.
    ```
    #py3
    text = "Updated Esctrip to Py3"
    encoded_text = base64.b64encode(text.encode())
    print("encoded string is", encoded_text.decode())

    ```

7. Run the following command to update the application:
    ```
    $ calm update app-migratable-bp azure-postgres-server - f appeditescript/blueprint.py
    ```
    The following output indicates that the task has been updated in the application:
    ```
    Application update is successful. Got Action Runlog uuid:
    40ba0cd0-60cc-4d01-97ff-3ad3516e3b7b
    Update messages:
    [App_profile.Default.Action.Custom Action1] Task 'B64
    usage task' updated in Application
    ```
    This command updates only the scripts of the tasks or variables in the application. Open the application and verify the updates.
  