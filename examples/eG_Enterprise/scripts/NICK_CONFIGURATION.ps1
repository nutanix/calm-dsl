$text1 = "[NICKNAME]"
$text2 = "Nick=@@{NICK_NAME}@@"
$text1 | Set-Content 'C:\eGurkha\agent\config\eg_nick.ini'
$text2 | Add-Content 'C:\eGurkha\agent\config\eg_nick.ini'