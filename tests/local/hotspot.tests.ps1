$ErrorActionPreference = 'Stop'
$script = Join-Path $PSScriptRoot '../../scripts/local/Connect-Hotspot.ps1'
$fakeAdb = Join-Path ([IO.Path]::GetTempPath()) ('hotspot-adb-' + [Guid]::NewGuid().ToString('N') + '.ps1')
Set-Content -LiteralPath $fakeAdb -Value @'
$global:HotspotCalls.Add(($args -join ' '))
$global:LASTEXITCODE = 0
if ('get-state' -in $args) { 'device' }
'@
function Get-NetIPAddress { param($AddressFamily, $IPAddress, $ErrorAction) @{ InterfaceIndex = 7 } }
function Get-NetIPConfiguration { param($InterfaceIndex) @{ IPv4DefaultGateway = @{ NextHop = '10.108.140.192' } } }
function Invoke-RestMethod { param($Uri, $TimeoutSec) $global:HotspotHealthUri = $Uri }
function Start-Sleep { param($Seconds) }
function Assert-Hotspot($Condition, $Message) { if (!$Condition) { throw $Message } }
try {
    $global:HotspotCalls = New-Object 'System.Collections.Generic.List[string]'
    & $script -Adb $fakeAdb
    Assert-Hotspot ($global:HotspotHealthUri -eq 'http://127.0.0.1:8080/health/ready') 'Health check must stay local.'
    Assert-Hotspot ($global:HotspotCalls.Contains('-d tcpip 5555')) 'Initial setup must target USB explicitly.'
    Assert-Hotspot ($global:HotspotCalls.Contains('-s 10.108.140.192:5555 reverse tcp:8080 tcp:8080')) 'Reverse must target the hotspot phone, not the PC.'
    $global:HotspotCalls.Clear()
    & $script -Adb $fakeAdb -Reconnect -ApiPort 8090
    Assert-Hotspot (!$global:HotspotCalls.Contains('-d tcpip 5555')) 'Reconnect must not require USB.'
    Assert-Hotspot ($global:HotspotCalls.Contains('-s 10.108.140.192:5555 reverse tcp:8080 tcp:8090')) 'Custom backend port was lost.'
    $global:HotspotCalls.Clear()
    & $script -Adb $fakeAdb -Stop
    Assert-Hotspot ($global:HotspotCalls.Count -eq 2) 'Stop must only reset and disconnect this phone.'
    Assert-Hotspot ($global:HotspotCalls[0] -eq '-s 10.108.140.192:5555 usb') 'Stop must restore USB mode.'
    Write-Host 'Hotspot USB setup, targeted network reconnect and cleanup tests passed.'
} finally {
    Remove-Item -LiteralPath $fakeAdb -Force
    Remove-Variable HotspotCalls, HotspotHealthUri -Scope Global -ErrorAction SilentlyContinue
}
