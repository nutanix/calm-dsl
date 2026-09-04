import os
from calm.dsl.builtins import *
from calm.dsl.builtins import (
    GlobalVariable,
    CalmVariable,
    Ref,
    ref,
    Metadata,
    CalmTask as CalmVarTask,
)
from calm.dsl.runbooks import RunbookTask as CalmTask
from calm.dsl.constants import PROJECT as PROJECT_CONSTANTS


SimpleGlobalVar1 = GlobalVariable(
    definition=CalmVariable.Simple(
        "abc",
        label="",
        description="",
    ),
    projects=[],
)


class GlobalVariableMetadata(Metadata):
    project = Ref.Project(PROJECT_CONSTANTS.DEFAULT_PROJECT_NAME)
