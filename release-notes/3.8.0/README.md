
# Major Feats

1. Added support to create python remote tasks that runs python script on remote machines, similar to ssh and powershell tasks. Use EXEC, SET_VARIABLE and DECISION class to make these remote python tasks.

    - `CalmTask.Exec.python(name="python_exec", filename=os.path.join("scripts", "escript_exec.py"), target=IPEndpoint)`
    - `CalmTask.SetVariable.python(name="python_exec", filename=os.path.join("scripts", "set_variable.py"), target=IPEndpoint)`
    - `CalmTask.Decision.python(name="python_exec", filename=os.path.join("scripts", "decision_script.py"), target=IPEndpoint)`


# Bug Fixes/Improvements

- **`Python 2 escripts will be deprecated from DSL v3.8.0 onwards.`**
- Default flow of escript is changed from python 2 to python 3 i.e. `CalmTask.Exec.escript, RunbookTask.Exec.escript, RunbookTask.Decision.escript, CalmTask.SetVariable.escript` will now point to python3 escripts.
- Migration support to upgrade python2 patch/update config tasks to python3 using command - `calm update app-migratable-bp`
- Delete orphan app of older tunnel post reset of tunnel VM using command - `calm reset network-group-tunnel-vm`
- Add ACP for Self Owned Access of report_config for project admin and acp for distributed_virtual_switch, recovery_point for all users in project. 
- Moved user and user group to project scope.


