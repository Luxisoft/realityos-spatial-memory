[CmdletBinding()]
param(
    [string]$EnvFile = '.env.local',
    [switch]$Reconnect,
    [switch]$Stop
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')

try {
    $values = Get-LocalEnvironment (Get-LocalRoot) $EnvFile
    $mode = if ($values['ANDROID_CONNECTION_MODE']) { $values['ANDROID_CONNECTION_MODE'] } else { 'localhost' }
    if ($mode -notin @('localhost', 'hotspot')) { throw 'ANDROID_CONNECTION_MODE must be localhost or hotspot.' }
    $adb = if ($values['ANDROID_ADB_PATH']) { $values['ANDROID_ADB_PATH'] } else { 'C:\platform-tools\adb.exe' }
    $port = if ($values['LOCAL_HTTP_PORT']) { [int]$values['LOCAL_HTTP_PORT'] } else { 8080 }
    if ($port -lt 1 -or $port -gt 65535) { throw 'LOCAL_HTTP_PORT must be between 1 and 65535.' }
    if (!(Test-Path -LiteralPath $adb -PathType Leaf)) { throw "ADB not found: $adb. Set ANDROID_ADB_PATH in $EnvFile." }

    if ($mode -eq 'hotspot') {
        $pcIp = $values['ANDROID_HOTSPOT_PC_IP']
        if (!$pcIp) { throw 'Set ANDROID_HOTSPOT_PC_IP to the PC Wi-Fi IPv4 address from ipconfig.' }
        & (Join-Path $PSScriptRoot 'Connect-Hotspot.ps1') -PcIp $pcIp -Adb $adb -ApiPort $port -Reconnect:$Reconnect -Stop:$Stop
        if (!$?) { throw 'Hotspot connection failed.' }
        return
    }
    if ($Stop) { throw '-Stop is only used in hotspot mode. Stop the hotspot before changing modes.' }
    $null = Invoke-RestMethod -Uri "http://127.0.0.1:$port/health/ready" -TimeoutSec 10
    # Default selection supports the existing USB or paired Wi-Fi connection,
    # and ADB refuses to choose when several devices are connected.
    & $adb get-state
    if ($LASTEXITCODE -ne 0) { throw 'Connect exactly one authorized ADB device (USB or existing wireless connection).' }
    & $adb reverse tcp:8080 "tcp:$port"
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the localhost tunnel.' }
    & $adb shell am start -n com.luxisoft.realityos.local/com.luxisoft.realityos.MainActivity
    if ($LASTEXITCODE -ne 0) { throw 'Could not open the installed local APK.' }
    Write-Host '[SUCCESS] Localhost connection ready using the existing ADB device.'
} catch {
    Write-Host ('[ERROR] ' + $_.Exception.Message)
    exit 1
}
