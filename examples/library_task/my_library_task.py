# my_library_task.py
from calm.dsl.builtins import Ref, Metadata
from calm.dsl.builtins import CalmTask


# Escript (Python 3)
Task1 = CalmTask.Exec.ssh(name="List Directory", script="ls")


class MyLibraryTask(Metadata):
    project = Ref.Project("auto_ncm_default")
