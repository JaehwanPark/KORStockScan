param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^https://')]
    [string]$ApiUrl,

    [Parameter(Mandatory = $true)]
    [string]$AccessKey,

    [Parameter(Mandatory = $true)]
    [string]$OrderAccessKey
)

$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$configDir = Join-Path $env:APPDATA 'KORStockScan\SamsungPriceWidget'
$configPath = Join-Path $configDir 'config.json'
$pythonw = (Get-Command pyw.exe -ErrorAction Stop).Source

New-Item -ItemType Directory -Path $configDir -Force | Out-Null
@{
    endpoint_url = $ApiUrl
    access_key = $AccessKey
    order_access_key = $OrderAccessKey
} | ConvertTo-Json | Set-Content -Path $configPath -Encoding UTF8

# %APPDATA% is already scoped to the interactive Windows user.  Tightening the
# file ACL is best-effort because some managed Windows profiles reject Set-Acl
# without SeSecurityPrivilege.  That must not prevent the shortcut install.
try {
    $acl = Get-Acl $configPath
    $acl.SetAccessRuleProtection($true, $false)
    $currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    $rule = New-Object System.Security.AccessControl.FileSystemAccessRule($currentUser, 'FullControl', 'Allow')
    $acl.SetAccessRule($rule)
    Set-Acl -Path $configPath -AclObject $acl
}
catch {
    Write-Warning 'Config ACL hardening was skipped; the inherited current-user AppData permissions remain in effect.'
}

$shell = New-Object -ComObject WScript.Shell
$desktopPath = [Environment]::GetFolderPath([Environment+SpecialFolder]::DesktopDirectory)
if ([string]::IsNullOrWhiteSpace($desktopPath)) {
    throw 'Windows Desktop directory could not be resolved.'
}
$shortcutPath = [System.IO.Path]::Combine($desktopPath, 'SamsungPriceWidget.lnk')
$shortcut = $shell.CreateShortcut([string]$shortcutPath)
$shortcut.TargetPath = $pythonw
$shortcut.Arguments = ('"{0}"' -f (Join-Path $scriptDir 'samsung_price_widget.py'))
$shortcut.WorkingDirectory = $scriptDir
$shortcut.Description = '삼성전자 현재가와 운영자 확인 수동주문'
$shortcut.Save()

Write-Host "바탕화면 바로가기를 만들었습니다: $shortcutPath"
