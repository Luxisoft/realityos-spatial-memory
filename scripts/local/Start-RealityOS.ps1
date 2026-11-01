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
foreach ($key in @('POSTGRES_PASSWORD', 'JWT_SECRET', 'DEVICE_CREDENTIAL_PEPPER', 'TTS_SERVICE_TOKEN')) {
    if (!$values[$key]) { $updates[$key] = New-LocalSecret }
}
if (!$values.MODEL_API_KEY) { $updates.MODEL_API_KEY = Read-LocalSecret 'Clave Meta propia (no se muestra)' }
if (!$values.LOCAL_ACCOUNT_EMAIL) { $updates.LOCAL_ACCOUNT_EMAIL = Read-Host 'Correo de tu cuenta local de prueba' }
if (!$values.LOCAL_ACCOUNT_PASSWORD) { $updates.LOCAL_ACCOUNT_PASSWORD = Read-LocalSecret 'Contrasena local de al menos 12 caracteres' }
if ($updates.Count) { Set-LocalEnvironment $root $updates }
$values = Get-LocalEnvironment $root
if (!$values.MODEL_API_KEY -or !$values.LOCAL_ACCOUNT_EMAIL -or $values.LOCAL_ACCOUNT_PASSWORD.Length -lt 12) {
    throw 'Completa la clave Meta, el correo y una contrasena de al menos 12 caracteres en .env.local.'
}
if ($info.NCPU -lt 4) { throw 'Asigna al menos 4 CPU a Docker Desktop para ejecutar el sistema completo.' }
Write-Host 'Comprobando CPU y memoria de Docker...'
$flags = Invoke-LocalDocker $root @('run', '--rm', '--pull', 'missing', '--entrypoint', 'cat', 'python:3.13-slim-trixie', '/proc/cpuinfo') -Quiet
$precision = $values.TTS_DTYPE
if ($precision -eq 'auto') {
    $precision = if ($flags -match '\b(avx512_bf16|amx_bf16)\b') { 'bfloat16' } else { 'float32' }
}
if ($precision -notin @('bfloat16', 'float32')) { throw 'TTS_DTYPE debe ser auto, bfloat16 o float32.' }
if ($precision -eq 'bfloat16' -and $flags -notmatch '\b(avx512_bf16|amx_bf16)\b') {
    throw 'Esta CPU no ofrece BF16 nativo. Utiliza TTS_DTYPE=auto o float32.'
}
$minimum = if ($precision -eq 'bfloat16') { 8GB } else { 12GB }
if ([double]$info.MemTotal -lt $minimum) { throw "Asigna al menos $($minimum / 1GB) GiB a Docker Desktop para esta CPU." }
$memory = if ($precision -eq 'bfloat16') { '4g' } else { '8g' }
Set-LocalEnvironment $root @{ LOCAL_TTS_MEMORY = $memory }
if (!$DockerDataDrive) { $DockerDataDrive = [IO.Path]::GetPathRoot($env:LOCALAPPDATA) }
$drive = New-Object IO.DriveInfo($DockerDataDrive)
if (!$drive.IsReady -or $drive.AvailableFreeSpace -lt 25GB) {
    throw 'Se requieren 25 GiB libres en la unidad de datos de Docker. Si la moviste, indica -DockerDataDrive D:\.'
}
$disk = Invoke-LocalDocker $root @('run', '--rm', '--entrypoint', 'df', 'python:3.13-slim-trixie', '-Pk', '/') -Quiet
$lastRow = ($disk -split "`n")[-1].Trim() -split '\s+'
if ([double]$lastRow[3] * 1KB -lt 25GB) { throw 'El disco Linux de Docker necesita al menos 25 GiB libres.' }
Write-Host 'Construyendo la instalacion local. La primera descarga de modelos puede tardar.'
Invoke-LocalCompose $root @('build', 'api', 'frontend', 'display', 'seamless-tts')
Invoke-LocalCompose $root @('run', '--rm', '--no-deps', 'api', 'python', '/scripts/local/check_runtime.py', '--providers')
Invoke-LocalCompose $root @('up', '-d', '--wait', '--wait-timeout', '120', 'postgres', 'redis')
Invoke-LocalCompose $root @('run', '--rm', '--no-deps', 'api', 'alembic', 'upgrade', 'head')
Invoke-LocalCompose $root @('run', '--rm', '--no-deps', 'api', 'python', '/scripts/local/bootstrap.py')
Invoke-LocalCompose $root @('up', '-d', '--wait', '--wait-timeout', '3600')
try {
    Invoke-LocalCompose $root @('exec', '-T', 'api', 'python', '/scripts/local/check_runtime.py', '--speech')
} catch {
    Invoke-LocalCompose $root @('stop', 'seamless-tts')
    throw 'No se pudo verificar la voz real. Revisa recursos y ejecuta el diagnostico local; no se uso un modelo simulado.'
}
Write-Host "Listo: http://localhost:$($values.LOCAL_HTTP_PORT) | Display: /display/ | API: /v1/"
Write-Host "Cuenta local: $($values.LOCAL_ACCOUNT_EMAIL). Usa la contrasena que elegiste."
