from calm.dsl.builtins import Project
from calm.dsl.builtins import Provider, Ref


ACCOUNT = "HashiCorpVault_Cred_Provider"


class TestDemoProject(Project):
    """Test project"""

    providers = [
        Provider.Custom_Provider(
            account=Ref.Account(ACCOUNT),
        )
    ]
