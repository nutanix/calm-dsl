$VMName = "@@{VM_NAME}@@"

Stop-SCVirtualMachine $VMName
Start-Sleep 10
Remove-SCVirtualMachine $VMName