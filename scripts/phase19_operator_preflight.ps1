[CmdletBinding()]
param(
    [string] $Workspace = (Join-Path $HOME 'phase19-external-session')
)

$ErrorActionPreference = 'Stop'

$FrozenArtifact = 'e117b6550686cf5e0ff787d9bd7d85e83996db07'
$required = @{
    'PHANTOMX_EXECUTOR_ADDRESS' = 'current intended Polygon executor address'
    'PHANTOMX_EXPECTED_SIGNER_ADDRESS' = 'current expected production signer address'
    'PHANTOMX_PRIVATE_RELAY_NAME' = 'approved private relay name'
    'PHANTOMX_OPERATOR_ID' = 'operator identity'
    'PHANTOMX_WITNESS_ID' = 'independent witness identity'
}

$repoRoot = (git rev-parse --show-toplevel 2>$null).Trim()
if (-not $repoRoot) { throw 'BLOCKED: run this from the ghost-hunter-new repository' }
$head = (git rev-parse HEAD).Trim().ToLowerInvariant()
if ($head -ne $FrozenArtifact) {
    throw "BLOCKED: repository HEAD is $head; expected frozen engineering artifact $FrozenArtifact"
}

$missing = @()
foreach ($name in $required.Keys) {
    if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($name))) {
        $missing += "$name ($($required[$name]))"
    }
}
if ($missing.Count -gt 0) {
    Write-Host 'BLOCKED: missing non-secret external-session inputs:'
    $missing | ForEach-Object { Write-Host "  - $_" }
    Write-Host ''
    Write-Host 'Set these values in the external/operator environment only. Do not paste private keys, seed phrases, credentials, or authentication secrets into chat or the repository.'
    exit 2
}

$executor = [Environment]::GetEnvironmentVariable('PHANTOMX_EXECUTOR_ADDRESS')
$signer = [Environment]::GetEnvironmentVariable('PHANTOMX_EXPECTED_SIGNER_ADDRESS')
$relay = [Environment]::GetEnvironmentVariable('PHANTOMX_PRIVATE_RELAY_NAME')
$operator = [Environment]::GetEnvironmentVariable('PHANTOMX_OPERATOR_ID')
$witness = [Environment]::GetEnvironmentVariable('PHANTOMX_WITNESS_ID')

if ($executor -notmatch '^0x[0-9a-fA-F]{40}$') { throw 'BLOCKED: PHANTOMX_EXECUTOR_ADDRESS is not a valid 20-byte EVM address' }
if ($signer -notmatch '^0x[0-9a-fA-F]{40}$') { throw 'BLOCKED: PHANTOMX_EXPECTED_SIGNER_ADDRESS is not a valid 20-byte EVM address' }

& (Join-Path $repoRoot 'scripts/phase19_one_shot_external_session.ps1') `
    -Workspace $Workspace `
    -ArtifactCommit $FrozenArtifact `
    -Executor $executor `
    -Signer $signer `
    -PrivateRelay $relay `
    -Operator $operator `
    -Witness $witness
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ''
Write-Host 'PRECHECK COMPLETE: external session workspace and manifest prepared.'
Write-Host 'Parallel lanes A/B/C/D can now run against this same session.'
Write-Host 'Lane E remains gated on independently observed realized settlement.'
Write-Host 'Safety: LIVE SIGNING=BLOCKED; PUBLIC BROADCAST=BLOCKED; LIVE CAPITAL=LOCKED'
