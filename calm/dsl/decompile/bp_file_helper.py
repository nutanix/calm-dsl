from calm.dsl.decompile.render import render_template
from calm.dsl.decompile.service import render_service_template
from calm.dsl.decompile.package import render_package_template
from calm.dsl.decompile.vm_disk_package import render_vm_disk_package_template
from calm.dsl.decompile.substrate import render_substrate_template
from calm.dsl.decompile.deployment import render_deployment_template
from calm.dsl.decompile.profile import render_profile_template
from calm.dsl.decompile.credential import render_credential_template
from calm.dsl.decompile.blueprint import render_blueprint_template
from calm.dsl.decompile.variable import get_secret_variable_files
from calm.dsl.builtins import BlueprintType


def render_bp_file_template(cls, local_dir=None, spec_dir=None):

    if not isinstance(cls, BlueprintType):
        raise TypeError("{} is not of type {}".format(cls, BlueprintType))

    user_attrs = cls.get_user_attrs()
    user_attrs["name"] = cls.__name__
    user_attrs["description"] = cls.__doc__

    # Find default cred
    default_cred = cls.default_cred

    # Context for namespace (initialised by blueprint name)
    entity_context = "BP_{}".format(cls.__name__)

    credential_list = []
    cred_file_map = {}
    for index, cred in enumerate(cls.credentials):
        if cred.__name__ == default_cred.__name__:
            cred.default = True
        credential_list.append(render_credential_template(cred))

    # Map to store the [Name: Rendered template for entity]
    entity_name_text_map = {}

    # Edges map to store the edges (dependencies) between entities
    entity_edges = {}

    for service in cls.services:
        entity_name_text_map[service.__name__] = render_service_template(
            service, entity_context
        )

        # Edge from services to other entities
        for dep in service.dependencies:
            add_edges(entity_edges, dep.__name__, service.__name__)

    downloadable_img_list = []
    for package in cls.packages:
        if getattr(package, "__kind__") == "app_package":
            entity_name_text_map[package.__name__] = render_package_template(
                package, entity_context
            )

            # Edge from package to service
            for dep in package.services:
                add_edges(entity_edges, dep.__name__, package.__name__)

        else:
            downloadable_img_list.append(render_vm_disk_package_template(package))
            # Printing all the downloadable images at the top, so ignore its edges

    for substrate in cls.substrates:
        entity_name_text_map[substrate.__name__] = render_substrate_template(
            substrate, entity_context
        )

    deployments = []
    for profile in cls.profiles:
        entity_name_text_map[profile.__name__] = render_profile_template(
            profile, entity_context
        )

        # Deployments
        deployments.extend(profile.deployments)
        for dep in deployments:
            add_edges(entity_edges, dep.__name__, profile.__name__)

    for deployment in deployments:
        entity_name_text_map[deployment.__name__] = render_deployment_template(
            deployment, entity_context
        )

        # Edges from deployment to package
        for dep in deployment.packages:
            add_edges(entity_edges, dep.__name__, deployment.__name__)

        # Edges from deployment to substrate
        add_edges(entity_edges, deployment.substrate.__name__, deployment.__name__)

        # Other dependencies
        for dep in deployment.dependencies:
            add_edges(entity_edges, dep.__name__, deployment.__name__)

    # Getting the local files used for secrets
    var_files = get_secret_variable_files()

    dependepent_entities = []
    dependepent_entities = get_ordered_entities(entity_name_text_map, entity_edges)

    blueprint = render_blueprint_template(cls)
    user_attrs.update(
        {
            "secret_var_files": var_files,
            "credentials": credential_list,
            "vm_images": downloadable_img_list,
            "dependent_entities": dependepent_entities,
            "blueprint": blueprint,
        }
    )

    text = render_template("bp_file_helper.py.jinja2", obj=user_attrs)
    return text.strip()


def get_ordered_entities(entity_name_text_map, entity_edges):
    """Returns the list in which all rendered templates are ordered according to depedencies"""

    res_entity_list = []
    entity_indegree_count = {}

    # Initializing indegree to each entity by 0
    for entity_name in list(entity_name_text_map.keys()):
        entity_indegree_count[entity_name] = 0

    # Iterate over edges and update indegree count for each entity
    for entity_name, to_entity_list in entity_edges.items():
        for entity in to_entity_list:
            entity_indegree_count[entity] += 1

    # Queue to store entities having indegree 0
    queue = []

    # Push entities having indegree count 0
    for entity_name, indegree in entity_indegree_count.items():
        if indegree == 0:
            queue.append(entity_name)

    # Topological sort
    while queue:

        ql = len(queue)

        # Inserting entities in result
        for entity in queue:
            res_entity_list.append(entity_name_text_map[entity])

        while ql:
            # Popping the top element

            cur_entity = queue.pop(0)

            # Iterating its edges, and decrease the indegree of dependent entity by 1
            for to_entity in entity_edges.get(cur_entity, []):
                entity_indegree_count[to_entity] -= 1

                # If indegree is zero push to queue
                if entity_indegree_count[to_entity] == 0:
                    queue.append(to_entity)

            ql -= 1

    return res_entity_list


def add_edges(edges, from_entity, to_entity):
    """Add edges in map edges"""

    if not edges.get(from_entity):
        edges[from_entity] = []

    edges[from_entity].append(to_entity)
