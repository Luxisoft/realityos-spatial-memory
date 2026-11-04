[CmdletBinding()]
param([string]$DockerDataDrive = "")
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')
if ($env:OS -ne 'Windows_NT') { throw 'Este comando esta preparado para PowerShell en Windows con Docker Desktop.' }
$root = Get-LocalRoot
$info = Assert-LocalDocker $root -StartDesktop
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
if ($updates.Count) { Set-LocalEnvironment $root $updates }
$values = Get-LocalEnvironment $root
if (!$values.MODEL_API_KEY) { throw 'Completa MODEL_API_KEY con tu clave Meta en .env.local.' }
if ($info.NCPU -lt 4) { throw 'Asigna al menos 4 CPU a Docker Desktop para ejecutar el sistema completo.' }
if ([double]$info.MemTotal -lt 7900000000) { throw 'Asigna al menos 8 GiB a Docker Desktop para el sistema local.' }
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
Invoke-LocalCompose $root @('run', '--rm', '--no-deps', 'api', 'python', '/scripts/local/prepare_database.py')
Invoke-LocalCompose $root @('run', '--rm', '--no-deps', 'api', 'python', '/scripts/local/bootstrap.py')
Invoke-LocalCompose $root @('up', '-d', '--wait', '--wait-timeout', '3600')
Invoke-LocalCompose $root @('exec', '-T', 'api', 'python', '/scripts/local/bootstrap.py', '--queue')
Write-Host "Listo: http://localhost:$($values.LOCAL_HTTP_PORT)/docs | App Android local: selecciona una de las nueve cuentas."
Write-Host 'Los escenarios se inicializan una sola vez. Reiniciar conserva tus cambios y eliminaciones.'
