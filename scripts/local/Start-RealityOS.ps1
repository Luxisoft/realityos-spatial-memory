[CmdletBinding()]
param([string]$DockerDataDrive = "")
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')
if ($env:OS -ne 'Windows_NT') { throw 'Este comando esta preparado para PowerShell en Windows con Docker Desktop.' }
$root = Get-LocalRoot
$info = Assert-LocalDocker $root
if ($info.Architecture -notin @('amd64', 'x86_64')) { throw 'Esta instalacion local soporta Windows x64 / contenedores linux-amd64.' }
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
if (!$values.MODEL_API_KEY) { $updates.MODEL_API_KEY = Read-LocalSecret 'Clave Meta propia (no se muestra)' }
if (!$values.ELEVENLABS_API_KEY) { $updates.ELEVENLABS_API_KEY = Read-LocalSecret 'Clave ElevenLabs propia (no se muestra)' }
if (!$values.LOCAL_ACCOUNT_EMAIL) { $updates.LOCAL_ACCOUNT_EMAIL = Read-Host 'Correo de tu cuenta local de prueba' }
if (!$values.LOCAL_ACCOUNT_PASSWORD) { $updates.LOCAL_ACCOUNT_PASSWORD = Read-LocalSecret 'Contrasena local de al menos 12 caracteres' }
if ($updates.Count) { Set-LocalEnvironment $root $updates }
$values = Get-LocalEnvironment $root
if (!$values.MODEL_API_KEY -or !$values.ELEVENLABS_API_KEY -or !$values.LOCAL_ACCOUNT_EMAIL -or $values.LOCAL_ACCOUNT_PASSWORD.Length -lt 12) {
    throw 'Completa las claves Meta y ElevenLabs, el correo y una contrasena de al menos 12 caracteres en .env.local.'
}
if ($info.NCPU -lt 4) { throw 'Asigna al menos 4 CPU a Docker Desktop para ejecutar el sistema completo.' }
if ([double]$info.MemTotal -lt 8GB) { throw 'Asigna al menos 8 GiB a Docker Desktop para el sistema local.' }
if (!$DockerDataDrive) { $DockerDataDrive = [IO.Path]::GetPathRoot($env:LOCALAPPDATA) }
$drive = New-Object IO.DriveInfo($DockerDataDrive)
if (!$drive.IsReady -or $drive.AvailableFreeSpace -lt 25GB) {
    throw 'Se requieren 25 GiB libres en la unidad de datos de Docker. Si la moviste, indica -DockerDataDrive D:\.'
}
$disk = Invoke-LocalDocker $root @('run', '--rm', '--entrypoint', 'df', 'python:3.13-slim-trixie', '-Pk', '/') -Quiet
$lastRow = ($disk -split "`n")[-1].Trim() -split '\s+'
if ([double]$lastRow[3] * 1KB -lt 25GB) { throw 'El disco Linux de Docker necesita al menos 25 GiB libres.' }
Write-Host 'Construyendo la instalacion local. La primera descarga de modelos puede tardar.'
Invoke-LocalCompose $root @('build', 'api')
Invoke-LocalCompose $root @('run', '--rm', '--no-deps', 'api', 'python', '/scripts/local/check_runtime.py', '--providers')
Invoke-LocalCompose $root @('up', '-d', '--wait', '--wait-timeout', '120', 'postgres', 'redis')
Invoke-LocalCompose $root @('run', '--rm', '--no-deps', 'api', 'alembic', 'upgrade', 'head')
Invoke-LocalCompose $root @('run', '--rm', '--no-deps', 'api', 'python', '/scripts/local/bootstrap.py')
Invoke-LocalCompose $root @('up', '-d', '--wait', '--wait-timeout', '3600')
# Retire only browser containers belonging to the isolated local project.
foreach ($service in @('frontend', 'display')) {
    $retired = Invoke-LocalDocker $root @('ps', '-aq', '--filter', 'label=com.docker.compose.project=realityos-local', '--filter', "label=com.docker.compose.service=$service") -Quiet
    foreach ($containerId in ($retired -split "`n")) {
        if ($containerId.Trim()) {
            Invoke-LocalDocker $root @('stop', $containerId.Trim())
            Invoke-LocalDocker $root @('rm', $containerId.Trim())
        }
    }
}
try {
    Invoke-LocalCompose $root @('exec', '-T', 'api', 'python', '/scripts/local/check_runtime.py', '--speech')
} catch {
    throw 'No se pudo verificar la voz real. Revisa ElevenLabs y la conexion, y ejecuta el diagnostico local; no se uso un modelo simulado.'
}
Write-Host "Listo: API http://localhost:$($values.LOCAL_HTTP_PORT)/v1/ | App: Android"
Write-Host "Cuenta local: $($values.LOCAL_ACCOUNT_EMAIL). Usa la contrasena que elegiste."
