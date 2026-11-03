[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')
$root = Get-LocalRoot
$null = Assert-LocalDocker $root
Assert-LocalConfiguration (Get-LocalEnvironment $root)
# Explicit opt-in. The ordinary local installer never enables public demo credentials.
Invoke-LocalCompose $root @('exec', '-T', 'api', 'mkdir', '-p', '/tmp/realityos-postman')
foreach ($file in @('demo.json', 'provision.py')) {
    Invoke-LocalCompose $root @('cp', (Join-Path $root ('simulator/postman/' + $file)), ('api:/tmp/realityos-postman/' + $file))
}
Invoke-LocalCompose $root @('exec', '-T', 'api', 'python', '/tmp/realityos-postman/provision.py', '--realm', 'localhost', '--apply')
Write-Host 'Local Postman account ready. Import RealityOS.postman_collection.json and run Localhost requests / 00 Quick start.'
