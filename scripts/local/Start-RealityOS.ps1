[CmdletBinding()]
param([string]$DockerDataDrive = "")
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')
$activity = 'RealityOS local setup'
try {
    Write-LocalProgress $activity 0 10 'Checking Docker'
    if ($env:OS -ne 'Windows_NT') { throw 'This command requires PowerShell on Windows with Docker Desktop.' }
    $root = Get-LocalRoot
    $info = Assert-LocalDocker $root -StartDesktop
    if ($info.Architecture -notin @('amd64', 'x86_64')) { throw 'Local setup requires Windows x64 and Linux amd64 containers.' }

    Write-LocalProgress $activity 1 10 'Preparing private local configuration'
    $path = Join-Path $root '.env.local'
    if (!(Test-Path -LiteralPath $path)) {
        Copy-Item -LiteralPath (Join-Path $root '.env.local.example') -Destination $path
        Protect-LocalFile $path
    }
    $values = Get-LocalEnvironment $root
    Assert-LocalConfiguration $values
    $updates = @{}
    foreach ($key in @('POSTGRES_PASSWORD', 'JWT_SECRET', 'DEVICE_CREDENTIAL_PEPPER', 'STORAGE_ENCRYPTION_KEY')) {
        if (!$values[$key]) { $updates[$key] = New-LocalSecret }
    }
    if (!$values.MODEL_API_KEY) { $updates.MODEL_API_KEY = Read-LocalSecret 'Your Meta MODEL_API_KEY (hidden)' }
    if ($updates.Count) { Set-LocalEnvironment $root $updates }
    $values = Get-LocalEnvironment $root
    if (!$values.MODEL_API_KEY) { throw 'Set your Meta MODEL_API_KEY in the private .env.local file.' }

    Write-LocalProgress $activity 2 10 'Checking CPU, memory and storage'
    if ($info.NCPU -lt 4) { throw 'Allocate at least 4 CPU cores to Docker Desktop.' }
    if ([double]$info.MemTotal -lt 7900000000) { throw 'Allocate at least 8 GiB RAM to Docker Desktop.' }
    if (!$DockerDataDrive) { $DockerDataDrive = [IO.Path]::GetPathRoot($env:LOCALAPPDATA) }
    $drive = New-Object IO.DriveInfo($DockerDataDrive)
    if (!$drive.IsReady -or $drive.AvailableFreeSpace -lt 25GB) {
        throw 'Docker needs 25 GiB free storage. For a different data drive, use -DockerDataDrive D:\.'
    }
    $disk = Invoke-LocalDocker $root @('run', '--rm', '--entrypoint', 'df', 'python:3.13-slim-trixie', '-Pk', '/') -Quiet
    $lastRow = ($disk -split "`n")[-1].Trim() -split '\s+'
    if ([double]$lastRow[3] * 1KB -lt 25GB) { throw 'The Docker Linux disk needs at least 25 GiB free storage.' }

    Write-LocalProgress $activity 3 10 'Building the backend image; first-time downloads can take several minutes'
    Invoke-LocalCompose $root @('--progress', 'plain', 'build', 'api')
    Write-LocalProgress $activity 4 10 'Checking model availability'
    Invoke-LocalCompose $root @('run', '--rm', '--no-deps', 'api', 'python', '/scripts/local/check_runtime.py', '--providers')
    Write-LocalProgress $activity 5 10 'Starting PostgreSQL and Redis'
    Invoke-LocalCompose $root @('up', '-d', '--wait', '--wait-timeout', '120', 'postgres', 'redis')
    Write-LocalProgress $activity 6 10 'Preparing the database schema'
    Invoke-LocalCompose $root @('run', '--rm', '--no-deps', 'api', 'python', '/scripts/local/prepare_database.py')
    Write-LocalProgress $activity 7 10 'Preparing the existing local scenarios'
    Invoke-LocalCompose $root @('run', '--rm', '--no-deps', 'api', 'python', '/scripts/local/bootstrap.py')
    Write-LocalProgress $activity 8 10 'Starting the API and worker'
    Invoke-LocalCompose $root @('up', '-d', '--wait', '--wait-timeout', '3600')
    Write-LocalProgress $activity 9 10 'Queueing pending indexing'
    Invoke-LocalCompose $root @('exec', '-T', 'api', 'python', '/scripts/local/bootstrap.py', '--queue')
    Write-LocalProgress $activity 10 10 'Local setup completed'
    Write-Host "[SUCCESS] Ready: http://localhost:$($values.LOCAL_HTTP_PORT)/docs | Android: select one of the nine local accounts."
    Write-Host '[INFO] Scenarios are initialized once. Restarting preserves edits and deletions. Indexing continues in the worker.'
} finally {
    Write-Progress -Id 0 -Activity $activity -Completed
}
