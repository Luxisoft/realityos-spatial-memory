[CmdletBinding()]
param([switch]$ResumeWorker)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')
. (Join-Path $PSScriptRoot 'Update.Common.ps1')

try {
    if ($env:OS -ne 'Windows_NT') { throw 'This command requires PowerShell on Windows; Linux uses scripts/local/update.sh.' }
    if ($ResumeWorker) { Resume-LocalUpdateWorker (Get-LocalRoot) }
    else { Invoke-LocalUpdate (Get-LocalRoot) }
} catch {
    Write-Host ('[ERROR] ' + $_.Exception.Message)
    exit 1
}
