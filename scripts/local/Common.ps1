# Shared PowerShell 5.1+/7 helpers. Every Compose call is scoped to realityos-local.
Set-StrictMode -Version Latest
$script:LocalUpdateImage = $null
[Threading.Thread]::CurrentThread.CurrentUICulture = [Globalization.CultureInfo]::GetCultureInfo('en-US')

function Get-LocalRoot { return (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path }

function Get-LocalEnvironment([string]$Root, [string]$FileName = '.env.local') {
    $values = @{}
    $path = if ([IO.Path]::IsPathRooted($FileName)) { $FileName } else { Join-Path $Root $FileName }
    if (!(Test-Path -LiteralPath $path)) { return $values }
    foreach ($line in [IO.File]::ReadAllLines($path)) {
        if ($line -match '^\s*([A-Z][A-Z0-9_]*)=(.*)$') {
            $key = $Matches[1]; $value = $Matches[2].Trim()
            if ($value.StartsWith('"') -and $value.EndsWith('"')) {
                $value = [regex]::Unescape($value.Substring(1, $value.Length - 2)).Replace('$$', '$')
            } elseif ($value.StartsWith("'") -and $value.EndsWith("'")) {
                $value = $value.Substring(1, $value.Length - 2).Replace("\'", "'")
            }
            $values[$key] = $value
        }
    }
    return $values
}

function Protect-LocalFile([string]$Path) {
    if ($env:OS -eq 'Windows_NT') {
        $identity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
        & icacls.exe $Path /inheritance:r /grant:r "${identity}:(F)" /grant:r '*S-1-5-18:(F)' | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'Could not protect the local credentials file.' }
    } else { & chmod 600 $Path }
}

function Set-LocalEnvironment([string]$Root, [hashtable]$Updates) {
    $path = Join-Path $Root '.env.local'
    $rows = New-Object 'System.Collections.Generic.List[string]'
    foreach ($line in [IO.File]::ReadAllLines($path)) {
        if ($line -match '^\s*([A-Z][A-Z0-9_]*)=' -and $Updates.ContainsKey($Matches[1])) { continue }
        $rows.Add($line)
    }
    foreach ($key in ($Updates.Keys | Sort-Object)) {
        $value = [string]$Updates[$key]
        if ($value.Contains("`n") -or $value.Contains("`r")) { throw 'Local environment values must fit on a single line.' }
        $escaped = $value.Replace('\', '\\').Replace('"', '\"').Replace('$', '$$')
        $rows.Add($key + '="' + $escaped + '"')
    }
    $temporary = $path + '.' + [Guid]::NewGuid().ToString('N') + '.tmp'
    [IO.File]::WriteAllText($temporary, '', (New-Object Text.UTF8Encoding($false)))
    Protect-LocalFile $temporary
    try {
        [IO.File]::WriteAllText($temporary, ($rows -join "`n") + "`n", (New-Object Text.UTF8Encoding($false)))
        if (Test-Path -LiteralPath $path) { [IO.File]::Replace($temporary, $path, [NullString]::Value) }
        else { [IO.File]::Move($temporary, $path) }
        Protect-LocalFile $path
    } finally { if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force } }
}

function New-LocalSecret {
    $bytes = New-Object byte[] 32
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    return ([BitConverter]::ToString($bytes)).Replace('-', '').ToLowerInvariant()
}

function Read-LocalSecret([string]$Prompt) {
    $secure = Read-Host $Prompt -AsSecureString
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
}

function Write-LocalProgress([string]$Activity, [int]$Completed, [int]$Total, [string]$Status) {
    if ($Total -lt 1 -or $Completed -lt 0 -or $Completed -gt $Total) { throw 'Invalid progress step count.' }
    $percent = [int][Math]::Floor(100 * $Completed / $Total)
    $filled = [int][Math]::Floor(20 * $Completed / $Total)
    $bar = ('#' * $filled) + ('-' * (20 - $filled))
    $level = if ($Completed -eq $Total) { 'SUCCESS' } else { 'INFO' }
    Write-Host "[$level] [$bar] $percent% | $Status ($Completed/$Total steps complete)"
    # Use one text renderer: Windows PowerShell's overlay can corrupt VS Code
    # terminal output when mixed with streamed status messages.
}

function Protect-LocalConsoleText([string]$Text, [hashtable]$Values) {
    foreach ($key in ($Values.Keys | Sort-Object { ([string]$Values[$_]).Length } -Descending)) {
        if ($key -match '(PASSWORD|TOKEN|SECRET|KEY|PEPPER)' -and $Values[$key].Length -gt 0) {
            $Text = $Text.Replace($Values[$key], '[redacted]')
        }
    }
    $Text = $Text -replace '\x1b\[[0-9;]*[A-Za-z]', ''
    if ($Text.Length -gt 300) { $Text = $Text.Substring(0, 297) + '...' }
    return $Text
}

function Write-LocalDockerSummary([string]$Line, [hashtable]$Values, [hashtable]$State) {
    $State.LastLine = $Line
    $message = ''
    $level = 'INFO'
    if ($Line -match '(?i)(\bwarning\b|\bwarn:|\berror\b|\bfailed\b|^denied:|^unauthorized:)') {
        $level = if ($Line -match '(?i)\bwarning\b|\bwarn:') { 'WARNING' } else { 'ERROR' }
        $message = Protect-LocalConsoleText $Line $Values
        if ($level -eq 'ERROR') { $State.ErrorShown = $true }
    } elseif ($Line -match '^#\d+ .*load (build definition|metadata|build context)') {
        $message = 'Preparing the backend build context and base image.'
    } elseif ($Line -match '^#\d+ .*RUN apt-get') {
        $message = 'Installing system and Python dependencies.'
    } elseif ($Line -match '^#\d+ .*RUN python .*FaceAnalysis') {
        $message = 'Preparing computer vision models.'
    } elseif ($Line -match '^#\d+ .*COPY simulator/') {
        $message = 'Copying the existing local scenarios.'
    } elseif ($Line -match '^#\d+ exporting') {
        $message = 'Exporting the backend image. This can take several minutes.'
    } elseif ($Line -match '^(api|worker|postgres|redis): ') {
        $message = Protect-LocalConsoleText $Line $Values
    } elseif ($Line -match '^Available local accounts: \d+$') {
        $message = $Line
    } elseif ($Line.StartsWith('{') -and $Line.Contains('models_available')) {
        $message = 'Meta API: the required models are available.'
    }
    if ($message -and $State.Seen.Add("$level $message")) { Write-Host "[$level] $message" }
}

function Invoke-LocalDocker([string]$Root, [string[]]$DockerArguments, [switch]$Quiet, [switch]$AllowFailure, [string]$InputText) {
    $values = Get-LocalEnvironment $Root
    if ($values.ContainsKey('REALITYOS_LOCAL_IMAGE')) { throw 'REALITYOS_LOCAL_IMAGE is reserved for the updater; remove it from .env.local.' }
    if ($script:LocalUpdateImage -and $script:LocalUpdateImage -notmatch '^sha256:[0-9a-f]{64}$') { throw 'Invalid internal local image pin.' }
    $saved = @{}
    # An exported production password/image/URL must not override .env.local.
    foreach ($key in $values.Keys) {
        if ($key -match '^(DOCKER|COMPOSE)_') { continue }
        $saved[$key] = [Environment]::GetEnvironmentVariable($key, 'Process')
        Remove-Item -LiteralPath ('Env:' + $key) -ErrorAction SilentlyContinue
    }
    if (!$saved.ContainsKey('REALITYOS_LOCAL_IMAGE')) {
        $saved['REALITYOS_LOCAL_IMAGE'] = [Environment]::GetEnvironmentVariable('REALITYOS_LOCAL_IMAGE', 'Process')
    }
    Remove-Item Env:REALITYOS_LOCAL_IMAGE -ErrorAction SilentlyContinue
    if ($script:LocalUpdateImage) {
        $env:REALITYOS_LOCAL_IMAGE = $script:LocalUpdateImage
    }
    $previous = $ErrorActionPreference
    $lines = New-Object 'System.Collections.Generic.List[string]'
    $summary = @{ Seen = New-Object 'System.Collections.Generic.HashSet[string]'; LastLine = ''; ErrorShown = $false }
    try {
        $ErrorActionPreference = 'Continue'
        $receive = {
            if ($Quiet) { $lines.Add([string]$_) }
            else { Write-LocalDockerSummary ([string]$_) $values $summary }
        }
        if ($PSBoundParameters.ContainsKey('InputText')) {
            $InputText | & docker @DockerArguments 2>&1 | ForEach-Object $receive
        } else {
            & docker @DockerArguments 2>&1 | ForEach-Object $receive
        }
        $code = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previous
        foreach ($key in $saved.Keys) {
            if ($null -eq $saved[$key]) { Remove-Item -LiteralPath ('Env:' + $key) -ErrorAction SilentlyContinue }
            else { [Environment]::SetEnvironmentVariable($key, $saved[$key], 'Process') }
        }
    }
    # Readiness probes can fail while Desktop starts. Do not print Docker's
    # empty server JSON or parse it as a running engine.
    if ($code -ne 0 -and $AllowFailure) { return }
    if ($Quiet -and $code -ne 0) {
        foreach ($line in $lines) {
            Write-LocalDockerSummary $line $values $summary
        }
    }
    if ($code -ne 0) {
        if (!$summary.ErrorShown -and $summary.LastLine) {
            Write-Host ('[ERROR] ' + (Protect-LocalConsoleText $summary.LastLine $values))
        }
        throw "Docker could not complete the local operation (exit code $code). Check the error above."
    }
    if ($Quiet) { return ($lines -join "`n") }
}

function Get-LocalComposeArguments([string]$Root, [string[]]$Command) {
    return @('compose', '--project-name', 'realityos-local', '--env-file', (Join-Path $Root '.env.local'),
        '--file', (Join-Path $Root 'infrastructure/docker-compose.local.yml')) + $Command
}

function Get-LocalBuildArguments([switch]$NoCache) {
    $arguments = @('--progress', 'plain', 'build')
    if ($NoCache) { $arguments += '--no-cache' }
    return $arguments + @('api')
}

function Invoke-LocalCompose([string]$Root, [string[]]$Command, [switch]$Quiet) {
    Invoke-LocalDocker -Root $Root -DockerArguments (Get-LocalComposeArguments $Root $Command) -Quiet:$Quiet
}

function Test-LocalDockerEndpoint([string]$Endpoint) {
    if ($Endpoint.StartsWith('npipe:') -or $Endpoint.StartsWith('unix:')) { return $true }
    try { $uri = [Uri]$Endpoint } catch { return $false }
    return $uri.Scheme -eq 'tcp' -and $uri.Host -in @('localhost', '127.0.0.1', '[::1]', '::1')
}

function Get-LocalDockerInfo([string]$Root) {
    if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
        throw 'Docker was not found. Install Docker Desktop and open a new terminal.'
    }
    if ($env:DOCKER_HOST -and !(Test-LocalDockerEndpoint $env:DOCKER_HOST)) {
        throw 'Remote Docker endpoints are refused. Select your local Docker Desktop context.'
    }
    $context = Invoke-LocalDocker $Root @('context', 'inspect', '--format', '{{json .Endpoints.docker.Host}}') -Quiet
    if (!(Test-LocalDockerEndpoint ($context | ConvertFrom-Json))) { throw 'A local Docker context is required.' }
    $output = Invoke-LocalDocker $Root @('info', '--format', '{{json .}}') -Quiet -AllowFailure
    if ($output) { return ($output | ConvertFrom-Json) }
}

function Start-LocalDockerDesktop {
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA 'Programs/DockerDesktop/Docker Desktop.exe'),
        (Join-Path $env:ProgramFiles 'Docker/Docker/Docker Desktop.exe')
    )
    $desktop = $candidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
    if (!$desktop) {
        throw 'Docker Desktop was not found. Install it or open your custom installation, then run this command again.'
    }
    Write-Host '[INFO] Starting Docker Desktop. On first launch, complete its setup in the application.'
    Start-Process -FilePath $desktop -WindowStyle Hidden -ErrorAction Stop | Out-Null
}

function Assert-LocalDocker([string]$Root, [switch]$StartDesktop, [int]$StartupTimeoutSeconds = 120) {
    $info = Get-LocalDockerInfo $Root
    if (!$info -and $StartDesktop -and $env:OS -eq 'Windows_NT') {
        Start-LocalDockerDesktop
        $deadline = (Get-Date).AddSeconds($StartupTimeoutSeconds)
        while (!$info) {
            # Desktop may change the selected context during startup; recheck
            # locality before every probe instead of trusting the first context.
            $info = Get-LocalDockerInfo $Root
            if ($info -or (Get-Date) -ge $deadline) { break }
            Write-Host '[INFO] Waiting for the Docker Desktop Linux engine...'
            Start-Sleep -Seconds 5
        }
    }
    if (!$info) {
        throw 'The local Docker engine is not responding. Open Docker Desktop, complete its first-run setup and wait for the engine. Check WSL2 and docker context ls; docker info must show Server without errors. Then run this command again.'
    }
    if ($info.OSType -ne 'linux') { throw 'Enable Linux containers / WSL2 in Docker Desktop.' }
    return $info
}

function Assert-LocalConfiguration([hashtable]$Values) {
    if ($Values.ContainsKey('REALITYOS_LOCAL_IMAGE')) { throw 'REALITYOS_LOCAL_IMAGE is reserved for the updater; remove it from .env.local.' }
    foreach ($key in $Values.Keys) {
        if ($key -match '^(DOCKER|COMPOSE)_') { throw 'Do not set DOCKER_* or COMPOSE_* in .env.local.' }
    }
    if ($Values.ENVIRONMENT -ne 'local' -or $Values.LOCAL_LOGIN_ENABLED -ne 'true' -or
        $Values.LOCAL_EVALUATION_ENABLED -ne 'true' -or $Values.META_MODE -ne 'live' -or $Values.FACE_ENGINE -ne 'insightface') {
        throw 'Startup requires the local environment, local account selection and real AI (live / insightface).'
    }
    foreach ($key in @('META_API_BASE_URL', 'META_GATEWAY_BASE_URL')) {
        if ($Values[$key] -match '(realityos|meta)\.luxisoft\.com') { throw 'Local configuration must not depend on the production server.' }
    }
    if ($Values.LOCAL_HTTP_PORT -notmatch '^\d+$' -or [int]$Values.LOCAL_HTTP_PORT -lt 1024 -or [int]$Values.LOCAL_HTTP_PORT -gt 65535) {
        throw 'LOCAL_HTTP_PORT must be a port between 1024 and 65535.'
    }
}
