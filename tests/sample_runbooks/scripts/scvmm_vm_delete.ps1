$VMName = "@@{VM_NAME}@@"
Write-Output '@@{credential_blob}@@'

Stop-SCVirtualMachine $VMName
Start-Sleep 10
Remove-SCVirtualMachine $VMName