$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '../../scripts/local/Common.ps1')
function Assert-Condition($Condition, [string]$Message) { if (!$Condition) { throw $Message } }
$root = Join-Path ([IO.Path]::GetTempPath()) ('RealityOS local tests ' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $root | Out-Null
try {
    Copy-Item (Join-Path (Get-LocalRoot) '.env.local.example') (Join-Path $root '.env.local')
    $production = Join-Path $root '.env'
    [IO.File]::WriteAllText($production, 'production must remain untouched')
    $before = [IO.File]::ReadAllText($production)
    $password = 'real-local-test $value "quoted" \folder and apostrophe''s'
    Set-LocalEnvironment $root @{ LOCAL_ACCOUNT_PASSWORD = $password; MODEL_API_KEY = 'local-test-key-for-script'; LOCAL_ACCOUNT_EMAIL = 'owner@local.test' }
    $values = Get-LocalEnvironment $root
    Assert-Condition ($values.LOCAL_ACCOUNT_PASSWORD -ceq $password) 'Password escaping is not lossless.'
    Assert-LocalConfiguration $values
    Set-LocalEnvironment $root @{ ELEVENLABS_VOICE_ID = 'JBFqnCBsd6RMkjVDRZzb' }
    $again = Get-LocalEnvironment $root
    Assert-Condition ($again.MODEL_API_KEY -ceq $values.MODEL_API_KEY) 'A restart replaced the Meta key.'
    Assert-Condition ($again.LOCAL_ACCOUNT_PASSWORD -ceq $password) 'A restart replaced the password.'
    Assert-Condition (([IO.File]::ReadAllText($production)) -ceq $before) 'Production configuration was touched.'
    $bytes = [IO.File]::ReadAllBytes((Join-Path $root '.env.local'))
    Assert-Condition (!($bytes[0] -eq 239 -and $bytes[1] -eq 187 -and $bytes[2] -eq 191)) 'The dotenv file has a BOM.'
    $arguments = Get-LocalComposeArguments $root @('down')
    Assert-Condition ($arguments[2] -ceq 'realityos-local') 'Wrong Docker project.'
    Assert-Condition ($arguments[4] -ceq (Join-Path $root '.env.local')) 'Wrong environment file.'
    Assert-Condition ($arguments[-1] -ceq 'down' -and '-v' -notin $arguments) 'Stopping would delete volumes.'
    Assert-Condition ($arguments[6].EndsWith('docker-compose.local.yml')) 'Production Compose was selected.'
    foreach ($endpoint in @('ssh://production', 'tcp://198.51.100.10:2375', 'https://server')) {
        Assert-Condition (!(Test-LocalDockerEndpoint $endpoint)) 'A remote Docker endpoint was accepted.'
    }
    foreach ($endpoint in @('unix:///var/run/docker.sock', 'npipe:////./pipe/dockerDesktopLinuxEngine', 'tcp://127.0.0.1:2375')) {
        Assert-Condition (Test-LocalDockerEndpoint $endpoint) 'A local Docker endpoint was rejected.'
    }
    $values.META_MODE = 'mock'
    $rejected = $false
    try { Assert-LocalConfiguration $values } catch { $rejected = $true }
    Assert-Condition $rejected 'The local startup accepted a simulated provider.'
    $values.META_MODE = 'live'; $values.META_API_BASE_URL = 'https://meta.luxisoft.com/v1'
    $rejected = $false
    try { Assert-LocalConfiguration $values } catch { $rejected = $true }
    Assert-Condition $rejected 'The local startup accepted a production Meta dependency.'
    $previousPassword = $env:POSTGRES_PASSWORD
    $env:POSTGRES_PASSWORD = 'external-production-environment'
    function docker {
        $global:FakeDockerPassword = $env:POSTGRES_PASSWORD
        $global:LASTEXITCODE = 0
        'checked'
    }
    $null = Invoke-LocalDocker $root @('info') -Quiet
    Assert-Condition ([string]::IsNullOrEmpty($global:FakeDockerPassword)) 'An exported production password reached Docker.'
    Assert-Condition ($env:POSTGRES_PASSWORD -ceq 'external-production-environment') 'The caller environment was not restored.'
    [Environment]::SetEnvironmentVariable('POSTGRES_PASSWORD', $previousPassword, 'Process')
    Remove-Item Function:docker
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        $previousError = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        $null = & docker compose version 2>&1
        $composeAvailable = $LASTEXITCODE -eq 0
        $ErrorActionPreference = $previousError
        if ($composeAvailable) {
            $updates = @{}
            foreach ($key in @('POSTGRES_PASSWORD', 'JWT_SECRET', 'DEVICE_CREDENTIAL_PEPPER')) { $updates[$key] = New-LocalSecret }
            Set-LocalEnvironment $root $updates
            New-Item -ItemType Directory -Path (Join-Path $root 'infrastructure') | Out-Null
            Copy-Item (Join-Path (Get-LocalRoot) 'infrastructure/docker-compose.local.yml') (Join-Path $root 'infrastructure/docker-compose.local.yml')
            $model = Invoke-LocalCompose $root @('config', '--format', 'json') -Quiet | ConvertFrom-Json
            Assert-Condition ($model.services.api.environment.LOCAL_ACCOUNT_PASSWORD.Replace('$$', '$') -ceq $password) 'Compose changed password escaping.'
            Assert-Condition ($model.name -ceq 'realityos-local') 'Compose rendered a different project.'
        }
    }
    Write-Host 'PowerShell isolation, credentials, escaping, restart and remote-context tests passed.'
} finally { Remove-Item -LiteralPath $root -Recurse -Force }
