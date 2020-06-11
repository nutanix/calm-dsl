from calm.dsl.builtins import AhvProject, get_subnet_ref, get_user_ref


class AbhiProject(AhvProject):

    subnets = [
        get_subnet_ref(name="vlan.0", cluster="calmdev1")
    ]
    
    users = [
        get_user_ref(display_name="sspuser2", name="sspuser1@systest.nutanix.com", directory_service="ST_AUTO_PC_AD")
    ]

class AbhiProjectPayload(AhvProject):

    user_roles = {
        AbhiProject.users[1] : "Consumer"
    }


