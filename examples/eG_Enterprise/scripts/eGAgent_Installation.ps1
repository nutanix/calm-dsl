$userpassword = ConvertTo-SecureString -asPlainText -Force -String "@@{URL_PASSWORD}@@"
$credential = New-Object System.Management.Automation.PSCredential("@@{URL_USERNAME}@@",$userpassword)

$FileName = Split-Path @@{EXE_FILE_URL}@@ -Leaf
$ISSFilename = Split-Path @@{ISS_FILE_URL}@@ -Leaf

$Destination = "C:\Users\"+$env:Username+"\Downloads\"+$FileName
$ISSDestination ="C:\Users\"+$env:Username+"\Downloads\"+$ISSFilename

Write-output "Downloading the eGAgent and iss files"
Invoke-WebRequest -Uri @@{EXE_FILE_URL}@@ -OutFile $Destination -Credential $credential 
Invoke-WebRequest -Uri @@{ISS_FILE_URL}@@ -OutFile $ISSDestination -Credential $credential

Write-output "eGAgent and iss files got downloaded"
Write-output "Installing the eGAgent"

Start-Process $Destination -ArgumentList "-a -s /f1${ISSDestination}" -Wait
Write-output "eGAgent installation completed"

$Setupfile_path = "C:\Users\"+$env:Username+"\Downloads\setup.log"
$result = Select-String -Path $Setupfile_path -Pattern "RESULTCODE"
Write-Output $result