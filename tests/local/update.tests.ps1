# All Docker commands below are simulated, including probes and Compose parsing.
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '../../scripts/local/Common.ps1')
. (Join-Path $PSScriptRoot '../../scripts/local/Update.Common.ps1')
function Assert-Condition($Condition, [string]$Message) { if (!$Condition) { throw $Message } }
$root = Join-Path ([IO.Path]::GetTempPath()) ('RealityOS update tests ' + [Guid]::NewGuid().ToString('N'))
$originalRoot = Get-LocalRoot
$script:installedImage = 'sha256:' + ('a' * 64)
$saved = @{}
foreach ($key in @('DOCKER_HOST', 'DOCKER_CONTEXT', 'MODEL_API_KEY', 'REALITYOS_LOCAL_IMAGE')) { $saved[$key] = [Environment]::GetEnvironmentVariable($key, 'Process') }
$script:calls = New-Object 'System.Collections.Generic.List[object]'
$script:scenario = ''

function docker {
    $a = @($args | ForEach-Object { [string]$_ })
    $global:LASTEXITCODE = 0
    $script:calls.Add(@{ Arguments = $a; Image = $env:REALITYOS_LOCAL_IMAGE; Key = $env:MODEL_API_KEY })
    switch ($a[0]) {
        'context' { if ($script:scenario -eq 'remote') { '"ssh://production"' } else { '"unix:///fake/docker.sock"' }; return }
        'info' { '{"OSType":"linux","Architecture":"amd64"}'; return }
        'image' { if ($script:scenario -eq 'missing-image') { $global:LASTEXITCODE = 1 } else { $script:installedImage }; return }
        'inspect' {
            if ($a[-2] -eq '{{.State.Running}}') { ([string]$script:oldWorkerRunning).ToLowerInvariant(); return }
            $service = $a[-1].Replace('id-', '')
            $current = $script:installedImage; $health = 'healthy'; $realm = 'ENVIRONMENT=local;LOCAL_LOGIN_ENABLED=true;LOCAL_EVALUATION_ENABLED=true;'
            $running = 'true'
            if ($script:scenario -eq 'stopped-worker' -and $service -eq 'worker') { $running = 'false' }
            if ($script:scenario -eq 'mixed-images' -and $service -eq 'worker') { $current = 'sha256:' + ('b' * 64) }
            if ($script:scenario -eq 'database-unhealthy' -and $service -eq 'postgres') { $health = 'unhealthy' }
            if ($script:scenario -eq 'server-realm') { $realm = 'ENVIRONMENT=production;' }
            "realityos-local|$service|$current|$running|$health|$realm"; return
        }
        'run' {
            $body = ($input | Out-String)
            if (!$body.Contains('def verify_image') -or $a[-2] -ne '-') { $global:LASTEXITCODE = 8; 'ERROR: probe was not piped to installed Python'; return }
            if ($a[-1] -ne $script:expectedHash) { $global:LASTEXITCODE = 8; 'ERROR: checkout hash is not normalized'; return }
            if ($script:scenario -eq 'dependencies') { $global:LASTEXITCODE = 8; 'Dependencies changed. Run the full local installer first.' }
            return
        }
        'exec' {
            $body = ($input | Out-String)
            if (!$body -or ($a[-1] -ne 'recover' -and $a[-1] -notmatch '^[0-9a-f]{32}$') -or $a[2] -ne 'id-worker') { $global:LASTEXITCODE = 8; 'ERROR: invalid worker probe'; return }
            if ($a[-2] -eq 'prepare' -and $script:scenario -in @('worker-busy', 'worker-unknown', 'resume-failed')) { $global:LASTEXITCODE = 8; 'ERROR: worker busy or status unavailable'; return }
            if ($a[-2] -eq 'resume' -and $script:scenario -eq 'resume-failed') { $global:LASTEXITCODE = 8; 'ERROR: restore unavailable'; return }
            return
        }
        'compose' {
            $command = $a[7]; $service = $a[-1]
            if ($command -eq 'ps') { if ($script:scenario -ne "missing-$service") { "id-$service" }; return }
            if ($command -eq 'config' -and $script:scenario -eq 'config-failed') { $global:LASTEXITCODE = 7; 'ERROR: invalid Compose configuration'; return }
            if ($command -eq 'stop' -and $script:scenario -eq 'stop-failed') { $global:LASTEXITCODE = 7; 'ERROR: simulated partial stop failure'; return }
            if ($command -eq 'stop') { $script:oldWorkerRunning = $false }
            if (($command -eq 'up' -and $script:scenario -eq "failed-$service") -or ($command -eq 'exec' -and $script:scenario -eq 'queue-failed')) { $global:LASTEXITCODE = 7; 'ERROR: simulated startup failure'; return }
            return
        }
    }
    $global:LASTEXITCODE = 9
    'ERROR: unexpected Docker command'
}

function Run-UpdateCase([string]$Scenario, [string]$Expected = '', [switch]$Recovery) {
    $script:scenario = $Scenario; $script:calls.Clear()
    $script:oldWorkerRunning = $true
    $errorText = ''
    try { if ($Recovery) { Resume-LocalUpdateWorker $root } else { Invoke-LocalUpdate $root } } catch { $errorText = $_.Exception.Message }
    if ($Expected) { Assert-Condition ($errorText -like "*$Expected*") "$Scenario expected '$Expected'; got '$errorText'." }
    else { Assert-Condition (!$errorText) "$Scenario failed: $errorText" }
    Assert-Condition ($env:REALITYOS_LOCAL_IMAGE -eq 'external-untrusted-image:latest') 'Caller image environment changed.'
    Assert-Condition ($env:MODEL_API_KEY -eq 'external-private-key') 'Caller credential environment changed.'
    Assert-Condition (!$script:LocalUpdateImage) 'Image pin survived the update.'
    Assert-Condition (([IO.File]::ReadAllText((Join-Path $root '.env'))) -eq 'do not change server configuration') 'Server configuration changed.'
    foreach ($call in $script:calls) {
        Assert-Condition (!$call.Key) 'An exported credential reached Docker.'
        Assert-Condition ($call.Image -ne 'external-untrusted-image:latest') 'An exported image reached Docker.'
        Assert-Condition ('build' -notin $call.Arguments -and 'pull' -notin $call.Arguments -and '--providers' -notin $call.Arguments -and 'down' -notin $call.Arguments) 'Heavy/destructive operation was invoked.'
        if ($call.Arguments[0] -eq 'run') {
            Assert-Condition ('--read-only' -in $call.Arguments -and '--network' -in $call.Arguments -and 'none' -in $call.Arguments -and '--env-file' -notin $call.Arguments -and '--volume' -notin $call.Arguments) 'Probe was not isolated.'
        }
    }
}

try {
    foreach ($path in @('backend/app', 'backend/alembic', 'backend/schema', 'scripts/local', 'simulator/database', 'simulator/media', 'infrastructure')) { New-Item -ItemType Directory -Path (Join-Path $root $path) -Force | Out-Null }
    foreach ($path in @('backend/alembic.ini', 'scripts/local/bootstrap.py')) { [IO.File]::WriteAllText((Join-Path $root $path), '') }
    [IO.File]::WriteAllText((Join-Path $root '.env'), 'do not change server configuration')
    $project = "[project]`nname='local-check'`n"
    [IO.File]::WriteAllText((Join-Path $root 'backend/pyproject.toml'), $project.Replace("`n", "`r`n"), (New-Object Text.UTF8Encoding($false)))
    $sha = [Security.Cryptography.SHA256]::Create()
    try { $script:expectedHash = [BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($project))).Replace('-', '').ToLowerInvariant() } finally { $sha.Dispose() }
    $envText = [IO.File]::ReadAllText((Join-Path $originalRoot '.env.local.example'))
    foreach ($key in @('POSTGRES_PASSWORD', 'JWT_SECRET', 'DEVICE_CREDENTIAL_PEPPER', 'STORAGE_ENCRYPTION_KEY', 'MODEL_API_KEY')) { $envText = $envText.Replace("$key=", "$key=local-test-value") }
    [IO.File]::WriteAllText((Join-Path $root '.env.local'), $envText)
    $env:DOCKER_HOST = ''; $env:DOCKER_CONTEXT = ''
    $env:MODEL_API_KEY = 'external-private-key'; $env:REALITYOS_LOCAL_IMAGE = 'external-untrusted-image:latest'

    foreach ($iteration in 1..2) {
        Run-UpdateCase 'success'
        $changes = @($script:calls | Where-Object { $_.Arguments[0] -eq 'compose' -and $_.Arguments[7] -in @('stop', 'up', 'exec') })
        Assert-Condition ($changes.Count -eq 4) 'Wrong number of mutation commands.'
        Assert-Condition (($changes[0].Arguments[-3..-1] -join ' ') -eq 'stop api worker') 'API/worker were not stopped together.'
        Assert-Condition ($changes[1].Arguments[-1] -eq 'api' -and $changes[2].Arguments[-1] -eq 'worker' -and $changes[3].Arguments[-1] -eq '--queue') 'Wrong startup/queue order.'
        foreach ($call in $changes[1..2]) {
            foreach ($flag in @('--no-build', '--pull', 'never', '--no-deps', '--force-recreate', '--wait')) { Assert-Condition ($flag -in $call.Arguments) "Missing startup flag $flag." }
            Assert-Condition ($call.Image -eq $script:installedImage) 'Recreation did not use the installed image ID.'
        }
        $pause = @($script:calls | Where-Object { $_.Arguments[0] -eq 'exec' -and $_.Arguments[-2] -eq 'prepare' })
        Assert-Condition ($pause.Count -eq 1 -and $script:calls.IndexOf($pause[0]) -lt $script:calls.IndexOf($changes[0])) 'Worker was not paused before stop.'
    }
    Run-UpdateCase 'stopped-worker'
    Assert-Condition (@($script:calls | Where-Object { $_.Arguments[0] -eq 'exec' }).Count -eq 0) 'Retry tried to execute a guard in a stopped worker.'
    $failures = @{
        dependencies = 'Docker could not complete'; 'missing-image' = 'Local image is missing'; 'mixed-images' = 'different images';
        'database-unhealthy' = 'must be running and healthy'; 'server-realm' = 'local evaluation realm'; remote = 'local Docker context';
        'missing-api' = 'not installed'; 'missing-worker' = 'not installed'; 'missing-postgres' = 'not installed'; 'missing-redis' = 'not installed'; 'config-failed' = 'Docker could not complete';
        'worker-busy' = 'Docker could not complete'; 'worker-unknown' = 'Docker could not complete'; 'resume-failed' = 'Docker could not complete'
    }
    foreach ($case in $failures.Keys) {
        Run-UpdateCase $case $failures[$case]
        Assert-Condition (@($script:calls | Where-Object { $_.Arguments[0] -eq 'compose' -and $_.Arguments[7] -in @('stop', 'up', 'exec') }).Count -eq 0) "$case stopped a service before preflight passed."
        if ($case -like 'worker-*' -or $case -eq 'resume-failed') { Assert-Condition ($script:calls[-1].Arguments[-2] -eq 'resume') 'Worker pause was not restored after rejected preparation.' }
    }
    foreach ($case in @('failed-api', 'failed-worker', 'queue-failed', 'stop-failed')) {
        Run-UpdateCase $case 'Docker could not complete'
        $last = $script:calls[-1].Arguments
        if ($case -eq 'stop-failed') { Assert-Condition ($last[0] -eq 'exec' -and $last[2] -eq 'id-worker' -and $last[-2] -eq 'resume') 'A partial stop failure did not restore its old consumer.' }
        else { Assert-Condition ($last[0] -eq 'inspect') 'Recovery tried to execute in a stopped old container.' }
        Assert-Condition (@($script:calls | Where-Object { $_.Arguments[0] -eq 'compose' -and $_.Arguments[7] -eq 'stop' }).Count -eq 1) 'A failed update stopped a worker that could be processing new jobs.'
        if ($case -eq 'failed-api') { Assert-Condition (@($script:calls | Where-Object { $_.Arguments[0] -eq 'compose' -and $_.Arguments[7] -eq 'up' -and $_.Arguments[-1] -eq 'worker' }).Count -eq 0) 'Worker started before API readiness.' }
    }
    Run-UpdateCase 'dependencies' -Recovery
    Assert-Condition (@($script:calls | Where-Object { $_.Arguments[0] -in @('run', 'image') -or ($_.Arguments[0] -eq 'compose' -and $_.Arguments[7] -ne 'ps') }).Count -eq 0) 'Explicit recovery checked dependencies or changed services.'
    Assert-Condition ($script:calls[-1].Arguments[-1] -eq 'recover') 'Explicit recovery did not use the recovery guard.'
    Run-UpdateCase 'stopped-worker' -Recovery
    Assert-Condition (@($script:calls | Where-Object { $_.Arguments[0] -eq 'exec' }).Count -eq 0) 'Recovery tried to execute in a stopped worker.'
    [IO.File]::WriteAllText((Join-Path $root '.env.local'), $envText + "`nREALITYOS_LOCAL_IMAGE=malicious`n")
    Run-UpdateCase 'reserved-image' 'reserved for the updater'
    Assert-Condition ($script:calls.Count -eq 0) 'Reserved image reached Docker.'
    [IO.File]::WriteAllText((Join-Path $root '.env.local'), $envText)
    $env:DOCKER_HOST = 'ssh://production'
    Run-UpdateCase 'remote-host' 'Remote Docker endpoints'
    Assert-Condition ($script:calls.Count -eq 0) 'Remote host reached Docker.'
    $env:DOCKER_HOST = ''
    Remove-Item -LiteralPath (Join-Path $root '.env.local') -Force
    Run-UpdateCase 'not-installed' 'Start-RealityOS.ps1 first'
    Assert-Condition ($script:calls.Count -eq 0) 'First installation reached Docker.'
    Write-Output '26 PowerShell fast-update scenarios passed; all Docker commands were simulated.'
} finally {
    foreach ($key in $saved.Keys) { [Environment]::SetEnvironmentVariable($key, $saved[$key], 'Process') }
    Remove-Item -LiteralPath $root -Recurse -Force
}
