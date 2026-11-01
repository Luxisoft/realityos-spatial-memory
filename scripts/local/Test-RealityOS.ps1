[CmdletBinding()]
param([switch]$Speech)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')
$root = Get-LocalRoot
$null = Assert-LocalDocker $root
Assert-LocalConfiguration (Get-LocalEnvironment $root)
Invoke-LocalCompose $root @('ps')
$command = @('exec', '-T', 'api', 'python', '/scripts/local/check_runtime.py')
if ($Speech) { $command += '--speech' }
Invoke-LocalCompose $root $command
