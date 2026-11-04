[CmdletBinding()]
param(
    [string]$PcIp = '10.108.140.109',
    [string]$Adb = 'C:\platform-tools\adb.exe',
    [ValidateRange(1, 65535)][int]$ApiPort = 8080,
    [switch]$Reconnect,
    [switch]$Stop
)
$ErrorActionPreference = 'Stop'

function Invoke-HotspotAdb([string[]]$Arguments) {
    $output = & $Adb @Arguments
    if ($LASTEXITCODE -ne 0) { throw "ADB failed: $($Arguments -join ' ')" }
    return $output
}

try {
    if (!(Test-Path -LiteralPath $Adb -PathType Leaf)) { throw "ADB not found: $Adb. Use -Adb with its installed path." }
    $addresses = @(Get-NetIPAddress -AddressFamily IPv4 -IPAddress $PcIp -ErrorAction SilentlyContinue)
    if ($addresses.Count -ne 1) { throw "PC address $PcIp is not active. Check ipconfig and pass -PcIp with the current Wi-Fi IPv4 address." }
    $network = Get-NetIPConfiguration -InterfaceIndex $addresses[0].InterfaceIndex
    $phoneIp = $network.IPv4DefaultGateway.NextHop
    if (!$phoneIp) { throw 'No IPv4 gateway found on the selected PC interface.' }
    $target = "${phoneIp}:5555"
    Write-Host "Hotspot: PC $PcIp -> phone $target"

    if ($Stop) {
        # Return this phone to USB debugging; do not reset unrelated ADB devices.
        Invoke-HotspotAdb @('-s', $target, 'usb')
        Invoke-HotspotAdb @('disconnect', $target)
        Write-Host 'Hotspot ADB stopped. Reconnect USB and run adb -d reverse tcp:8080 tcp:8080 for the usual setup.'
        return
    }

    $null = Invoke-RestMethod -Uri "http://127.0.0.1:$ApiPort/health/ready" -TimeoutSec 10
    if (!$Reconnect) {
        # -d refuses ambiguous selection and only addresses a USB device.
        Invoke-HotspotAdb @('-d', 'get-state')
        Invoke-HotspotAdb @('-d', 'tcpip', '5555')
        Start-Sleep -Seconds 2
    }
    Invoke-HotspotAdb @('connect', $target)
    # adb connect can report connection failure with exit code zero.
    $state = Invoke-HotspotAdb @('-s', $target, 'get-state')
    if (($state -join '').Trim() -ne 'device') { throw "Phone $target is not authorized and connected." }
    Invoke-HotspotAdb @('-s', $target, 'reverse', 'tcp:8080', "tcp:$ApiPort")
    Invoke-HotspotAdb @('-s', $target, 'shell', 'am', 'start', '-n', 'com.luxisoft.realityos.local/com.luxisoft.realityos.MainActivity')
    Write-Host '[SUCCESS] Network tunnel ready. You can unplug USB; keep the PC connected to this phone hotspot.'
} catch {
    Write-Host ('[ERROR] ' + $_.Exception.Message)
    Write-Host 'Keep USB connected if the phone blocks ADB on its hotspot. No backend, APK or localhost configuration was changed.'
    exit 1
}
