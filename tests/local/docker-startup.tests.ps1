# All external commands are fakes: this suite never starts Desktop or calls Docker.
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '../../scripts/local/Common.ps1')

function Assert-Condition($Condition, [string]$Message) { if (!$Condition) { throw $Message } }
function Assert-Failure([scriptblock]$Action, [string]$Expected) {
    $message = ''
    try { & $Action | Out-Null } catch { $message = $_.Exception.Message }
    Assert-Condition ($message -like "*$Expected*") "Expected '$Expected', got '$message'."
}

$savedEnvironment = @{}
foreach ($key in @('DOCKER_HOST', 'DOCKER_CONTEXT', 'OS', 'LOCALAPPDATA', 'ProgramFiles', 'MODEL_API_KEY')) {
    $savedEnvironment[$key] = [Environment]::GetEnvironmentVariable($key, 'Process')
}

function Reset-FakeDocker {
    $script:engine = 'stopped'
    $script:endpoint = 'npipe:////./pipe/docker_engine'
    $script:desktopInstalled = $true
    $script:desktopStarts = 0
    $script:infoCalls = 0
    $script:sleeps = 0
    $script:readyAfterSleep = $false
    $script:remoteAfterSleep = $false
    $script:messages = New-Object 'System.Collections.Generic.List[string]'
    $env:DOCKER_HOST = ''
    $env:DOCKER_CONTEXT = ''
    $env:MODEL_API_KEY = 'test-exported-key'
}

function Get-LocalEnvironment([string]$Root) { return @{ MODEL_API_KEY = 'test-local-key' } }
function Write-Host([string]$Object) { $script:messages.Add($Object) }
function Test-Path([string]$LiteralPath, [string]$PathType) {
    return $script:desktopInstalled -and $LiteralPath.EndsWith('Docker Desktop.exe')
}
function Start-Process([string]$FilePath, [string]$WindowStyle, [string]$ErrorAction) {
    Assert-Condition ($FilePath.EndsWith('Docker Desktop.exe')) 'Unexpected process launched.'
    Assert-Condition ($WindowStyle -eq 'Hidden') 'Desktop must launch without a console window.'
    $script:desktopStarts++
}
function Start-Sleep([int]$Seconds) {
    $script:sleeps++
    if ($script:readyAfterSleep) { $script:engine = 'linux' }
    if ($script:remoteAfterSleep) { $script:endpoint = 'ssh://remote-server' }
}
function docker {
    $global:LASTEXITCODE = 0
    Assert-Condition ([string]::IsNullOrEmpty($env:MODEL_API_KEY)) 'An exported key reached Docker.'
    if ($args[0] -eq 'context') {
        return ('"' + $script:endpoint + '"')
    }
    if ($args[0] -ne 'info') { throw 'Unexpected Docker command.' }
    $script:infoCalls++
    if ($script:engine -eq 'stopped') {
        '{"OSType":"","RAW_SERVER_JSON":true}'
        Write-Error 'failed to connect to docker_engine; simulated missing pipe'
        $global:LASTEXITCODE = 1
        return
    }
    return ('{"OSType":"' + $script:engine + '","Architecture":"amd64","NCPU":4,"MemTotal":8589934592}')
}

try {
    $env:OS = 'Windows_NT'
    $env:LOCALAPPDATA = 'C:\Fake user\AppData\Local'
    $env:ProgramFiles = 'C:\Program Files'

    Reset-FakeDocker
    $script:engine = 'linux'
    $info = Assert-LocalDocker 'unused-test-root' -StartDesktop
    Assert-Condition ($info.OSType -eq 'linux' -and $info.NCPU -eq 4) 'Healthy engine information was lost.'
    Assert-Condition ($script:desktopStarts -eq 0 -and $script:sleeps -eq 0) 'Healthy engine was restarted.'

    Reset-FakeDocker
    $script:readyAfterSleep = $true
    $info = Assert-LocalDocker 'unused-test-root' -StartDesktop
    Assert-Condition ($info.OSType -eq 'linux') 'Stopped Desktop did not recover.'
    Assert-Condition ($script:desktopStarts -eq 1 -and $script:sleeps -eq 1) 'Startup was not retried.'
    Assert-Condition ($env:MODEL_API_KEY -eq 'test-exported-key') 'Caller environment was not restored.'
    Assert-Condition (($script:messages -join ' ') -notmatch 'RAW_SERVER_JSON|simulated missing pipe') 'Failed probes leaked raw output.'

    Reset-FakeDocker
    Assert-Failure { Assert-LocalDocker 'unused-test-root' -StartDesktop -StartupTimeoutSeconds 0 } 'El motor Docker local no responde'
    Assert-Condition ($script:desktopStarts -eq 1 -and $script:sleeps -eq 0) 'Startup wait is not bounded.'
    Assert-Condition ($env:MODEL_API_KEY -eq 'test-exported-key') 'Failed probe did not restore the caller environment.'

    Reset-FakeDocker
    Assert-Failure { Assert-LocalDocker 'unused-test-root' } 'docker info debe mostrar Server'
    Assert-Condition ($script:desktopStarts -eq 0) 'Diagnostics or shutdown started Desktop.'

    Reset-FakeDocker
    $script:desktopInstalled = $false
    Assert-Failure { Assert-LocalDocker 'unused-test-root' -StartDesktop } 'No se encontro Docker Desktop'
    Assert-Condition ($script:desktopStarts -eq 0) 'Missing Desktop was launched.'

    Reset-FakeDocker
    $env:DOCKER_HOST = 'ssh://remote-server'
    Assert-Failure { Assert-LocalDocker 'unused-test-root' -StartDesktop } 'remoto esta rechazado'
    Assert-Condition ($script:infoCalls -eq 0 -and $script:desktopStarts -eq 0) 'Remote host reached startup.'

    Reset-FakeDocker
    $script:endpoint = 'tcp://198.51.100.10:2375'
    Assert-Failure { Assert-LocalDocker 'unused-test-root' -StartDesktop } 'contexto Docker local'
    Assert-Condition ($script:infoCalls -eq 0 -and $script:desktopStarts -eq 0) 'Remote context reached startup.'

    Reset-FakeDocker
    $script:remoteAfterSleep = $true
    Assert-Failure { Assert-LocalDocker 'unused-test-root' -StartDesktop } 'contexto Docker local'
    Assert-Condition ($script:infoCalls -eq 2) 'Readiness retry contacted a remote engine.'

    Reset-FakeDocker
    $script:engine = 'windows'
    Assert-Failure { Assert-LocalDocker 'unused-test-root' -StartDesktop } 'Linux containers / WSL2'
    Assert-Condition ($script:desktopStarts -eq 0) 'Windows containers triggered a restart.'

    Write-Output '9 Docker startup regression cases passed (all external commands simulated).'
} finally {
    foreach ($key in $savedEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($key, $savedEnvironment[$key], 'Process')
    }
}
