"""
Redis Cluster (Blueprint consists of single pod)

"""


from calm.dsl.builtins import basic_cred
from calm.dsl.builtins import Service, Profile, Blueprint, PODDeployment
from calm.dsl.builtins import read_spec, read_local_file


ROOT_PASSWD = read_local_file("root_passwd")


class RedisService(Service):
    pass


class RedisK8SDeployment(PODDeployment):
    """ Redis Deployment on K8S """

    containers = [RedisService]
    deployment_spec = read_spec("deployment.yaml")
    service_spec = read_spec("service.yaml")


class RedisProfile(Profile):
    """ Application Profile """

    deployments = [RedisK8SDeployment]


class RedisK8SBlueprint(Blueprint):
    """ Sample K8S Blueprint """

    services = [RedisService]
    credentials = [basic_cred("root", ROOT_PASSWD, default=True)]
    profiles = [RedisProfile]


def main():
    print(RedisK8SBlueprint.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
