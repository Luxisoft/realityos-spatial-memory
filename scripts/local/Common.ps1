# Shared PowerShell 5.1+/7 helpers. Every Compose call is scoped to realityos-local.
Set-StrictMode -Version Latest

function Get-LocalRoot { return (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path }

function Get-LocalEnvironment([string]$Root) {
    $values = @{}
    $path = Join-Path $Root '.env.local'
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
        if ($LASTEXITCODE -ne 0) { throw 'No se pudo proteger el archivo local de credenciales.' }
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
        if ($value.Contains("`n") -or $value.Contains("`r")) { throw 'Los valores locales deben ocupar una sola linea.' }
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

function Invoke-LocalDocker([string]$Root, [string[]]$DockerArguments, [switch]$Quiet, [switch]$AllowFailure) {
    $values = Get-LocalEnvironment $Root
    $saved = @{}
    # An exported production password/image/URL must not override .env.local.
    foreach ($key in $values.Keys) {
        if ($key -match '^(DOCKER|COMPOSE)_') { continue }
        $saved[$key] = [Environment]::GetEnvironmentVariable($key, 'Process')
        Remove-Item -LiteralPath ('Env:' + $key) -ErrorAction SilentlyContinue
    }
    $previous = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $lines = @(& docker @DockerArguments 2>&1)
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
    if (!$Quiet -or $code -ne 0) {
        foreach ($line in $lines) {
            $text = [string]$line
            foreach ($key in $values.Keys) {
                if ($key -match '(PASSWORD|TOKEN|SECRET|KEY)' -and $values[$key].Length -gt 0) {
                    $text = $text.Replace($values[$key], '[redacted]')
                }
            }
            Write-Host $text
        }
    }
    if ($code -ne 0) { throw 'Docker no pudo completar la operacion local. Revisa el mensaje anterior.' }
    if ($Quiet) { return ($lines -join "`n") }
}

function Get-LocalComposeArguments([string]$Root, [string[]]$Command) {
    return @('compose', '--project-name', 'realityos-local', '--env-file', (Join-Path $Root '.env.local'),
        '--file', (Join-Path $Root 'infrastructure/docker-compose.local.yml')) + $Command
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
        throw 'No se encontro Docker. Instala Docker Desktop y abre una nueva terminal.'
    }
    if ($env:DOCKER_HOST -and !(Test-LocalDockerEndpoint $env:DOCKER_HOST)) {
        throw 'El contexto Docker remoto esta rechazado. Selecciona Docker Desktop local.'
    }
    $context = Invoke-LocalDocker $Root @('context', 'inspect', '--format', '{{json .Endpoints.docker.Host}}') -Quiet
    if (!(Test-LocalDockerEndpoint ($context | ConvertFrom-Json))) { throw 'Se requiere un contexto Docker local.' }
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
        throw 'No se encontro Docker Desktop. Instalalo o abre tu instalacion personalizada y vuelve a ejecutar el comando.'
    }
    Write-Host 'Iniciando Docker Desktop. Si es el primer inicio, completa su configuracion en la aplicacion.'
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
            Write-Host 'Esperando al motor Linux de Docker Desktop...'
            Start-Sleep -Seconds 5
        }
    }
    if (!$info) {
        throw 'El motor Docker local no responde. Abre Docker Desktop, completa su configuracion inicial y espera a que el motor este en ejecucion. Revisa WSL2 y el contexto con docker context ls; docker info debe mostrar Server sin errores. Despues vuelve a ejecutar el comando.'
    }
    if ($info.OSType -ne 'linux') { throw 'Activa Linux containers / WSL2 en Docker Desktop.' }
    return $info
}

function Assert-LocalConfiguration([hashtable]$Values) {
    foreach ($key in $Values.Keys) {
        if ($key -match '^(DOCKER|COMPOSE)_') { throw 'No definas DOCKER_* ni COMPOSE_* en .env.local.' }
    }
    if ($Values.ENVIRONMENT -ne 'local' -or $Values.LOCAL_LOGIN_ENABLED -ne 'true' -or
        $Values.LOCAL_EVALUATION_ENABLED -ne 'true' -or $Values.META_MODE -ne 'live' -or $Values.FACE_ENGINE -ne 'insightface') {
        throw 'Este arranque exige entorno local, cuenta local e IA real (live / insightface).'
    }
    foreach ($key in @('META_API_BASE_URL', 'META_GATEWAY_BASE_URL')) {
        if ($Values[$key] -match '(realityos|meta)\.luxisoft\.com') { throw 'El perfil local no debe depender del servidor de produccion.' }
    }
    if ($Values.LOCAL_HTTP_PORT -notmatch '^\d+$' -or [int]$Values.LOCAL_HTTP_PORT -lt 1024 -or [int]$Values.LOCAL_HTTP_PORT -gt 65535) {
        throw 'LOCAL_HTTP_PORT debe ser un puerto entre 1024 y 65535.'
    }
}
