from calm.dsl.builtins import AhvProject
from calm.dsl.builtins import Provider


class AbhiProject(AhvProject):

    provider_list = [
        Provider.Ntnx(name="NTNX_LOCAL_AZ"),
        Provider.Aws(name="AWS account"),
        Provider.Azure(name="AZURE_account"),
        Provider.Gcp(name="GCP Account"),
        Provider.Vmware(name="VMWARE account"),
        Provider.K8s(name="K8S_account_basic_auth"),
    ]


def main():
    print(AbhiProject.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
