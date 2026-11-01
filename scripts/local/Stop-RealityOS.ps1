[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')
$root = Get-LocalRoot
$null = Assert-LocalDocker $root
Assert-LocalConfiguration (Get-LocalEnvironment $root)
Invoke-LocalCompose $root @('down')
Write-Host 'Instalacion local detenida. Los datos y modelos se conservan.'
