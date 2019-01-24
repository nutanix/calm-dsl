'''
Sample single vm example to convert python dsl to calm v3 api spec

'''

import json

from scratch import Service, Substrate, Deployment, Profile, Blueprint

#TODO - Add Variable, Port classes


class MySQL(Service):
    #TODO - Add a sample mysql config with install/uninstall scripts
    pass


class AHVMedVM(Substrate):
    #TODO - Add code to load the right yaml file for create spec
    pass


class MySQLDeployment(Deployment):
    """Sample description for mysql db instance"""

    def __init__(self):
        self.add_substrate(AHVMedVM()) # AHV VM
        self.add_services([MySQL(), ]) # mysql service


class NxProfile(Profile):

    def __init__(self):
        self.add_deployments([MySQLDeployment(), ])


class MyBlueprint(Blueprint):
    """sample bp description"""

    def __init__(self):
        self.add_profiles([NxProfile(), ])



def main():

    bp = MyBlueprint()
    dct = dict()
    out = bp.dump(dct)
    # print(json.dumps(out))


if __name__ == "__main__":
    main()
