# Calm allows decompiling runbooks

## Runbook decompile command
- Decompile allows users to create the python representation of a runbook. Following command decompiles a runbook with the name as runbook_name from the configured calm service.
- Example: 
    ```
    calm decompile runbook <runbook_name>
    ```
- NOTE: Decompiling runbooks will not decompile secrets of runbook i.e. secret-variables, credential-secrets etc. For every secret, it will create a file with empty data in `.local` directory present in the decompiling directory.

#### Flags:

- `-f, --file FILE` to decompile from a filepath (optional)
- `-p, --prefix TEXT` appends this prefix for entities created (optional)
- `-d, --dir TEXT ` output path of the decompile operation (optional)

