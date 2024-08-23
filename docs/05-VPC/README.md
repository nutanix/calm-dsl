# Calm-DSL supports VPC & Overlay Subnets across entities:

1. Ability to Create, Delete, List and Reset VPC Tunnels through network-group-tunnels commands
2. Ability to Whitelist Cluster, VPC and Overlay Subnets in Projects & Environments
3. Ability specify Cluster in VM Spec and Overlay subnets in NICs in Environment
4. Ability to specify Cluster in VM Spec and Overlay subnets in NICs in Blueprints
5. Ability to specify Overlay subnets in NIC for App-Edit
6. Ability to specify Tunnel in IP and HTTP type Endpoints
7. Ability to specify Tunnel in Escript tasks in Runbooks and Blueprints
8. Decompile of Blueprints with Overlay Subnets
9. VPC Cache with Tunnel information
10. Subnets Cache expanded to store Overlay Subnets


## VPC Tunnels/Network Group Tunnels

Network Group Tunnels (network-group-tunnels) commands are available to perform Create, Delete, List and Reset of VPC Tunnels. VPC Tunnels are refrenced using Tunnel Name.

### Sample Commands

- calm create network_group_tunnel -f tunnel_file.py; Sample below of tunnel_file

    ```
    from calm.dsl.builtins import NetworkGroupTunnel
    from calm.dsl.builtins import Provider, Ref
    from calm.dsl.builtins.models.network_group_tunnel_vm_spec import ahv_network_group_tunnel_vm_spec

    class MyVPCTunnel(NetworkGroupTunnel):
      """My VPC Tunnel"""
      account = Ref.Account("NTNX_LOCAL_AZ")
      platform_vpcs = [Ref.Vpc("<vpc-name>", account_name="<account-name>")]
      tunnel_vm_spec = ahv_network_group_tunnel_vm_spec("<cluster-name>", "<overlay-subnet-name>")
    ```
    Example can also be found in examples.

- calm get network-group-tunnels - List of all VPC/Network Group Tunnels
- calm describe network-group-tunnel <tunnel-name> - Describes a VPC Tunnel
- calm delete network-group-tunnel <tunnel-name> - Deletes a VPC Tunnel
- calm reset network-group-tunnel-vm -f examples/NetworkGroupTunnel/network_group_tunnel.py -n <tunnel-name> - Reset VPC Tunnel.
  Resetting tunnel will spin up new VPC tunnel VM and delete older tunnel VM. Tunnel reference is not changed. Sample file below:
    ```
    from calm.dsl.builtins import NetworkGroupTunnelVMSpec

    class NewNetworkGroupTunnel1(NetworkGroupTunnelVMSpec):
        """Network group tunnel spec for reset"""
        cluster = "<cluster-name>"
        subnet = "<subnet-name>"
        type = "AHV"
    ```

## Project
- Calm-DSL supports whitelisting Cluster, VPC and Overlay Subnets

###  Sample Project with Cluster, VPC and Overlay Subnet

- User can use specify clusters, VPCs and Oberlay Subnets in Projects. Clusters whitelisting can be done for Projects with VLAN subnets also.
    ```
    class OverlaySubnetProject(Project):
    """Sample DSL Project"""

    providers = [
        Provider.Ntnx(
            account=Ref.Account("account-name"),
            subnets=[Ref.Subnet(name="vlan-name", cluster="cluster-name"),
             Ref.Subnet(name="overlay-subnet-name",vpc="vpc-name")],
            clusters=[Ref.Cluster(name="cluster-name", account_name="account-name")],
            vpcs=[Ref.Vpc(name="vpc-name", account_name="account-name")]
        ),
    ]
    ```

## Referencing Cluster, VPC, Overlay subnets across DSL constructs
- Built-in helpers to reference Cluster, VPC and Overlay Subnets in different constructs
   ```
      Ref.VPC(name=<VPC-name>, account_name=<account-name>)
      Ref.Subnet(name=<network-name>, vpc=<VPC-name>) # Overlay Subnet
      Ref.Subnet(name=<network-name>, cluster=<Cluster-name>) # VLAN Subnet
      Ref.Cluster(name=<cluster-name>, account_name=<account-name>)
   ```
- Existing constructs of Ref.Subnet() are still supported and backward compatible. Additional parameters of Cluster for VLAN subnets and
  VPC for Overlay subnets have been added to avoid same name conflicts and better readability.

## Cluster
- Can be used in Projects as described above
- Can be used within AhvVM in Blueprints and VM in Environment Sample -
  ```
    class MyVM(AhvVM):
      cluster = Ref.Cluster(name="cluster-name")
  ```

 ## Overlay Subnets
 - Can be used in Projects as described above
 - Can be used within AhvVmResources
  ```
    class MyVMResources(AhvVMResources)
      nics = [AhvVmNic(subnet="overlay-subnet", vpc="vpc-name")]
  ```
  - Can be used in App-Edit. Sample
  ```
   nics = [
        PatchField.Ahv.Nics.add(
            AhvVmNic(subnet="overlay-subnet", vpc="vpc-name"),
            editable=True,
        ),
    ]
  ```

 ## VPCs
 - Can be used in Projects & VPC Tunnels/Network Group Tunnels as described above

## Referencing Tunnels across DSL constructs
- Built-in helper to reference Tunnel in different constructs.
   ```
      Ref.Tunnel(name="tunnel-name")
   ```
- Can be used in Endpoints of type IP and HTTP. Sample below, Tunnel reference is accepted as an argument in Endpoint helpers.
  ```
    DslHTTPEndpoint = Endpoint.HTTP(
      URL, verify=True, auth=Endpoint.Auth(AUTH_USERNAME, AUTH_PASSWORD),
      tunnel=Ref.Tunnel(name=VPC_TUNNEL)
  ```
- Can be used in Escript based Tasks. Sample below. Tunnel reference is accepted as an argument in Task helpers.
  ```
    Task.SetVariable.escript(name="tunnel_set_var", filename="<file-name>", tunnel=Ref.Tunnel(name="tunnel-name"))
    Task.Exec.escript(name="tunnel_exec", filename="<file-name>", tunnel=Ref.Tunnel(name="tunnel-name"))
  ```
