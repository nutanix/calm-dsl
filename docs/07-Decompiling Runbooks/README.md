# Calm allows decompiling runbooks

## Runbook decompile command
Decompile allows users to create the python representation of a runbook. Following command decompiles a runbook with the name as runbook_name from the configured calm service
<br>
`calm decompile runbook <runbook_name>`

#### Flags:

- `-f, --file FILE` to decompile from a filepath (optional)
- `-p, --prefix TEXT` appends this prefix for entities created (optional)
- `-d, --dir TEXT ` output path of the decompile operation (optional)

