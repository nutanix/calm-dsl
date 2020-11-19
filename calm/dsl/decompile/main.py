from calm.dsl.decompile.action import init_action_globals
from calm.dsl.decompile.credential import init_cred_globals
from calm.dsl.decompile.variable import init_variable_globals
from calm.dsl.decompile.ref_dependency import init_ref_dependency_globals
from calm.dsl.decompile.file_handler import init_file_globals


def init_decompile_context():

    # Reinitializes context for decompile
    init_action_globals()
    init_cred_globals()
    init_file_globals()
    init_ref_dependency_globals()
    init_variable_globals()
