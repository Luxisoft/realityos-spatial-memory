# Preflight and restart are separate: no service stops until all checks pass.
function Get-LocalUpdateInstallation([string]$Root, [switch]$WorkerOnly) {
    if (!(Test-Path -LiteralPath (Join-Path $Root '.env.local') -PathType Leaf)) {
        throw 'No local installation found. Run scripts/local/Start-RealityOS.ps1 first.'
    }
    $values = Get-LocalEnvironment $Root
    Assert-LocalConfiguration $values
    foreach ($key in @('POSTGRES_PASSWORD', 'JWT_SECRET', 'DEVICE_CREDENTIAL_PEPPER', 'STORAGE_ENCRYPTION_KEY', 'MODEL_API_KEY')) {
        if (!$values[$key]) { throw "Missing $key in .env.local. Run scripts/local/Start-RealityOS.ps1 first." }
    }
    if (!$WorkerOnly) {
        foreach ($path in @('backend/app', 'backend/alembic', 'backend/alembic.ini', 'backend/schema', 'backend/pyproject.toml', 'scripts/local/bootstrap.py', 'simulator/database', 'simulator/media')) {
            if (!(Test-Path -LiteralPath (Join-Path $Root $path))) { throw "Missing repository source: $path. Finish updating the checkout first." }
        }
    }
    $info = Assert-LocalDocker $Root
    if ($info.Architecture -notin @('amd64', 'x86_64')) { throw 'Local evaluation requires Linux x64 containers.' }
    # Go raw strings survive Windows PowerShell 5.1 native argument forwarding.
    $template = '{{index .Config.Labels `com.docker.compose.project`}}|{{index .Config.Labels `com.docker.compose.service`}}|{{.Image}}|{{.State.Running}}|{{if .State.Health}}{{.State.Health.Status}}{{end}}|{{range .Config.Env}}{{if or (eq . `ENVIRONMENT=local`) (eq . `LOCAL_LOGIN_ENABLED=true`) (eq . `LOCAL_EVALUATION_ENABLED=true`)}}{{.}};{{end}}{{end}}'
    $image = ''
    $worker = ''; $workerRunning = $false
    $services = if ($WorkerOnly) { @('worker') } else { @('api', 'worker', 'postgres', 'redis') }
    foreach ($service in $services) {
        $id = Invoke-LocalCompose $Root @('ps', '--all', '--quiet', $service) -Quiet
        if (!$id -or $id.Trim() -match '\s') { throw "Local $service is not installed. Run scripts/local/Start-RealityOS.ps1 first." }
        $state = (Invoke-LocalDocker $Root @('inspect', '--type', 'container', '--format', $template, $id.Trim()) -Quiet).Trim().Split('|')
        if ($state.Count -ne 6 -or $state[0] -ne 'realityos-local' -or $state[1] -ne $service) { throw 'Refusing a container outside the local installation.' }
        if ($service -in @('postgres', 'redis')) {
            if ($state[3] -ne 'true' -or $state[4] -ne 'healthy') { throw "Local $service must be running and healthy. Start the existing local stack first; no services were stopped." }
        } else {
            foreach ($flag in @('ENVIRONMENT=local;', 'LOCAL_LOGIN_ENABLED=true;', 'LOCAL_EVALUATION_ENABLED=true;')) {
                if (!$state[5].Contains($flag)) { throw 'The installed API/worker is not in the local evaluation realm.' }
            }
            if ($image -and $image -ne $state[2]) { throw 'Installed API and worker use different images. Run the full local installer first.' }
            $image = $state[2]
            if ($service -eq 'worker') { $worker = $id.Trim(); $workerRunning = $state[3] -eq 'true' }
        }
    }
    if ($WorkerOnly) { return @{ Worker = $worker; WorkerRunning = $workerRunning } }
    if ($image -notmatch '^sha256:[0-9a-f]{64}$') { throw 'The installed local image ID is invalid.' }
    $installed = Invoke-LocalDocker $Root @('image', 'inspect', '--format', '{{.Id}}', $image) -Quiet -AllowFailure
    if (!$installed -or $installed.Trim() -ne $image) { throw 'Local image is missing. Run scripts/local/Start-RealityOS.ps1 first.' }
    $project = [IO.File]::ReadAllText((Join-Path $Root 'backend/pyproject.toml')).Replace("`r`n", "`n")
    $sha = [Security.Cryptography.SHA256]::Create()
    try { $hash = [BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($project))).Replace('-', '').ToLowerInvariant() }
    finally { $sha.Dispose() }
    $probe = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'check_update_image.py'))
    $null = Invoke-LocalDocker $Root @('run', '--rm', '--interactive', '--pull', 'never', '--network', 'none', '--read-only', '--entrypoint', 'python', $image, '-', $hash) -Quiet -InputText $probe
    return @{ Image = $image; Worker = $worker; WorkerRunning = $workerRunning }
}

function Invoke-LocalUpdate([string]$Root) {
    Write-LocalProgress 'RealityOS local update' 0 5 'Checking the installed local runtime'
    $installation = Get-LocalUpdateInstallation $Root
    $previousImage = $script:LocalUpdateImage
    $pauseAttempted = $false
    $token = [Guid]::NewGuid().ToString('N')
    $workerGuard = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'check_update_worker.py'))
    try {
        $script:LocalUpdateImage = $installation.Image
        # Render/validate the current Compose file before stopping either process.
        $null = Invoke-LocalCompose $Root @('config', '--quiet') -Quiet
        if ($installation.WorkerRunning) {
            Write-Host '[INFO] Checking that the worker has no active processing before pausing its consumer.'
            $pauseAttempted = $true
            $null = Invoke-LocalDocker $Root @('exec', '--interactive', $installation.Worker, 'python', '-', 'prepare', $token) -Quiet -InputText $workerGuard
        }
        Write-LocalProgress 'RealityOS local update' 1 5 'Stopping API and worker together'
        Invoke-LocalCompose $Root @('stop', 'api', 'worker')
        Write-LocalProgress 'RealityOS local update' 2 5 'Applying database updates and starting API'
        Invoke-LocalCompose $Root @('up', '-d', '--no-build', '--pull', 'never', '--no-deps', '--force-recreate', '--wait', '--wait-timeout', '180', 'api')
        Write-LocalProgress 'RealityOS local update' 3 5 'Starting worker with the same installed image'
        Invoke-LocalCompose $Root @('up', '-d', '--no-build', '--pull', 'never', '--no-deps', '--force-recreate', '--wait', '--wait-timeout', '60', 'worker')
        Write-LocalProgress 'RealityOS local update' 4 5 'Queuing only pending local publications'
        Invoke-LocalCompose $Root @('exec', '-T', 'api', 'python', '/scripts/local/bootstrap.py', '--queue')
        Write-LocalProgress 'RealityOS local update' 5 5 'Local update completed'
        Write-Host '[SUCCESS] Code and local data revisions are current. PostgreSQL, Redis, credentials and installed models were preserved.'
    } catch {
        $failure = $_
        if ($pauseAttempted) {
            # Resume only our old container/pause. A recreated worker may already
            # be processing new jobs and must never receive an unchecked stop.
            $running = Invoke-LocalDocker $Root @('inspect', '--type', 'container', '--format', '{{.State.Running}}', $installation.Worker) -Quiet -AllowFailure
            if ($running -and $running.Trim() -eq 'true') {
                try { $null = Invoke-LocalDocker $Root @('exec', '--interactive', $installation.Worker, 'python', '-', 'resume', $token) -Quiet -InputText $workerGuard }
                catch { Write-Host '[ERROR] Worker recovery could not be confirmed. After confirming no other update is running, run scripts/local/Update-RealityOS.ps1 -ResumeWorker before retrying.' }
            }
        }
        Write-Host '[ERROR] Update incomplete. PostgreSQL/Redis services and volumes were preserved. No additional processes were stopped; resolve the reported error before retrying.'
        throw $failure
    } finally {
        $script:LocalUpdateImage = $previousImage
    }
}

function Resume-LocalUpdateWorker([string]$Root) {
    $installation = Get-LocalUpdateInstallation $Root -WorkerOnly
    if (!$installation.WorkerRunning) { Write-Host '[INFO] Worker is stopped; rerun the regular updater to start it.'; return }
    $workerGuard = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'check_update_worker.py'))
    Invoke-LocalDocker $Root @('exec', '--interactive', $installation.Worker, 'python', '-', 'recover') -InputText $workerGuard
    Write-Host '[SUCCESS] Worker consumer recovery completed. No services were stopped or recreated.'
}
