# No real Docker commands, credentials or services are used by this suite.
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '../../scripts/local/Common.ps1')
function Assert-Condition($Condition, [string]$Message) { if (!$Condition) { throw $Message } }
function Get-LocalEnvironment([string]$Root) {
    return @{ MODEL_API_KEY = 'fake-private-key'; DEVICE_CREDENTIAL_PEPPER = 'fake-private-pepper' }
}
function Write-Host([string]$Object) { $script:messages.Add($Object) }
function Write-Progress([int]$Id, [string]$Activity, [string]$Status, [int]$PercentComplete, [switch]$Completed) {
    throw 'The native PowerShell progress overlay must not be mixed with console summaries.'
}
function Reset-Console {
    $script:messages = New-Object 'System.Collections.Generic.List[string]'
    $script:mode = 'build'
    $script:streamed = $false
}
function docker {
    $global:LASTEXITCODE = 0
    if ($script:mode -eq 'quiet') { return '{"OSType":"linux"}' }
    '#13 [9/14] RUN apt-get update && pip install .'
    '#13 101.1 Downloading opencv_python_headless.whl.metadata (19 kB)'
    '#13 101.8 Collecting stringzilla>=3.10.4'
    '#13 102.5 INFO: pip is looking at multiple versions of kombu[redis]'
    'WARNING: fake-private-key fake-private-pepper needs attention'
    $script:streamed = ($script:messages -join ' ') -match '\[WARNING\]'
    '#19 exporting to image'
    '#19 exporting layers'
    'api: Up 1 minute (healthy)'
    if ($script:mode -eq 'failure') {
        'ERROR: failed to download using fake-private-key'
        $global:LASTEXITCODE = 7
    } elseif ($script:mode -eq 'unclassified-failure') {
        'no space left on device; fake-private-key'
        $global:LASTEXITCODE = 8
    }
}

Reset-Console
Invoke-LocalDocker 'unused' @('build')
$output = $script:messages -join "`n"
Assert-Condition $script:streamed 'Warnings were buffered until Docker exited.'
Assert-Condition ($output -match 'Installing system and Python dependencies') 'Build phase summary is missing.'
Assert-Condition ($output -notmatch 'Collecting|Downloading|kombu|opencv|fake-private') 'Verbose output or a secret reached the console.'
Assert-Condition ($output -match '\[WARNING\].*\[redacted\]') 'Warning or redaction was lost.'
Assert-Condition ($output -match '\[INFO\] api: Up 1 minute \(healthy\)') 'Compact service status was lost.'
Assert-Condition (@($script:messages | Where-Object { $_ -match 'Exporting the backend image' }).Count -eq 1) 'Repeated phase messages were not collapsed.'

Reset-Console
$script:mode = 'quiet'
$result = Invoke-LocalDocker 'unused' @('info') -Quiet
Assert-Condition ($result -ceq '{"OSType":"linux"}') 'Machine-readable output changed.'
Assert-Condition ($script:messages.Count -eq 0) 'A quiet probe printed output.'

foreach ($failureMode in @('failure', 'unclassified-failure')) {
    Reset-Console
    $script:mode = $failureMode
    $failed = $false
    $failureMessage = ''
    try {
        Invoke-LocalDocker 'unused' @('build')
        Write-LocalProgress 'Test' 1 1 'Completed'
    } catch { $failureMessage = $_.Exception.Message; $failed = $failureMessage -match 'exit code [78]' }
    Assert-Condition $failed "Expected Docker failure, got: $failureMessage"
    $output = $script:messages -join ' '
    Assert-Condition ($output -match '\[ERROR\]' -and $output -notmatch 'fake-private') 'A failure was hidden or exposed a secret.'
    Assert-Condition ($output -notmatch '\[SUCCESS\]|100%') 'Failed work was marked complete.'
}

Reset-Console
$script:mode = 'failure'
$result = Invoke-LocalDocker 'unused' @('info') -Quiet -AllowFailure
Assert-Condition ($null -eq $result -and $script:messages.Count -eq 0) 'A failed readiness probe leaked output.'

Reset-Console
Write-LocalProgress 'Setup' 0 10 'Checking Docker'
Write-LocalProgress 'Setup' 3 10 'Building the backend image'
Write-LocalProgress 'Setup' 10 10 'Local setup completed'
Assert-Condition ($script:messages[0] -match '0%.*0/10' -and $script:messages[1] -match '30%.*3/10') 'Progress is not based on completed steps.'
Assert-Condition ($script:messages[2] -match '^\[SUCCESS\] \[####################\] 100%') 'Completion is not visible without an interactive host.'
Assert-Condition ((Get-LocalBuildArguments) -join ' ' -eq '--progress plain build api') 'Normal startup stopped reusing the build cache.'
Assert-Condition ((Get-LocalBuildArguments -NoCache) -join ' ' -eq '--progress plain build --no-cache api') 'A fresh build is not scoped to the local API image.'
Write-Output '7 console regression cases passed: live summaries, redaction, probes, errors, text progress and fresh builds.'
