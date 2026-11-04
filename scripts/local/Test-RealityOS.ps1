[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')
$activity = 'RealityOS local diagnostics'
try {
    Write-LocalProgress $activity 0 3 'Checking Docker and local configuration'
    $root = Get-LocalRoot
    $null = Assert-LocalDocker $root
    Assert-LocalConfiguration (Get-LocalEnvironment $root)
    Write-LocalProgress $activity 1 3 'Checking service status'
    Invoke-LocalCompose $root @('ps', '--format', '{{.Service}}: {{.Status}}')
    Write-LocalProgress $activity 2 3 'Checking model availability'
    Invoke-LocalCompose $root @('exec', '-T', 'api', 'python', '/scripts/local/check_runtime.py')
    Write-LocalProgress $activity 3 3 'Local diagnostics completed'
} finally {
    Write-Progress -Id 0 -Activity $activity -Completed
}
