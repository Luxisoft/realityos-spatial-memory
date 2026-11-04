[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')
$activity = 'RealityOS local shutdown'
try {
    Write-LocalProgress $activity 0 2 'Checking Docker and local configuration'
    $root = Get-LocalRoot
    $null = Assert-LocalDocker $root
    Assert-LocalConfiguration (Get-LocalEnvironment $root)
    Write-LocalProgress $activity 1 2 'Stopping local services'
    Invoke-LocalCompose $root @('down')
    Write-LocalProgress $activity 2 2 'Local services stopped; database and queue volumes are preserved'
} finally {
    Write-Progress -Id 0 -Activity $activity -Completed
}
