$JobGroupID1 = [Guid]::NewGuid().ToString()
$resource_blob = '@@{resources_blob}@@'
$resource_blob_obj = ConvertFrom-Json –InputObject $resource_blob
$VMName = $resource_blob_obj.vm_name
Write-Output '@@{credential_blob}@@'
$Template = Get-SCVMTemplate -VMMServer localhost -ID "9945c039-0a63-4346-83c8-a83cf87e61e6" | where {$_.Name -eq "Windows Server 2019"}
$HardwareProfile = Get-SCHardwareProfile -VMMServer localhost | where {$_.Name -eq "CustomProviderHP"}
$GuestOSProfile = Get-SCGuestOSProfile -VMMServer localhost | where {$_.Name -eq "CustomProviderGOP"}

$username = "administrator"
$password = ConvertTo-SecureString "nutanix/4u" -AsPlainText -Force
$LocalAdministratorCredential = New-Object System.Management.Automation.PSCredential -ArgumentList ($username, $password)

$OperatingSystem = Get-SCOperatingSystem -VMMServer localhost -ID "dffb90ce-abb0-4082-8764-fb08db195c05" | where {$_.Name -eq "Windows Server 2019 Standard"}

New-SCVMTemplate -Name "Temporary Template $($VMName)" -Template $Template -HardwareProfile $HardwareProfile -GuestOSProfile $GuestOSProfile -JobGroup $JobGroupID1 -ComputerName $VMName -TimeZone 190 -LocalAdministratorCredential $LocalAdministratorCredential  -Workgroup "WORKGROUP" -AnswerFile $null -OperatingSystem $OperatingSystem -UpdateManagementProfile $null 



$template = Get-SCVMTemplate -All | where { $_.Name -eq "Temporary Template $($VMName)" }
$virtualMachineConfiguration = New-SCVMConfiguration -VMTemplate $template -Name $VMName
Write-Output $virtualMachineConfiguration
$vmHost = Get-SCVMHost -ID "2721b12d-e176-4e19-918e-5c85053982dd"
Set-SCVMConfiguration -VMConfiguration $virtualMachineConfiguration -VMHost $vmHost
Update-SCVMConfiguration -VMConfiguration $virtualMachineConfiguration

$AllNICConfigurations = Get-SCVirtualNetworkAdapterConfiguration -VMConfiguration $virtualMachineConfiguration



Update-SCVMConfiguration -VMConfiguration $virtualMachineConfiguration
New-SCVirtualMachine -Name $VMName -VMConfiguration $virtualMachineConfiguration -Description "" -BlockDynamicOptimization $false -JobGroup $JobGroupID1 -StartAction "AlwaysAutoTurnOnVM" -StopAction "SaveVM"
while (Get-SCJob -Running | where {$_.ResultName -eq $VMName}){
    Start-Sleep 10
}
Start-SCVirtualMachine $VMName

if ($(Get-SCVirtualNetworkAdapter -VM $VMName | select IPv4Addresses -ExpandProperty IPv4Addresses) -eq $Null){
    Start-Sleep 10
    Read-SCVirtualMachine -VM $VMName
}
$IpAddress = Get-SCVirtualNetworkAdapter -VM $VMName | select IPv4Addresses -ExpandProperty IPv4Addresses
Write-Output "IpAddress=$($IpAddress)"