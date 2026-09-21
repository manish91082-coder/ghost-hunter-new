[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)] [string] $Workspace,
    [Parameter(Mandatory = $true)] [ValidatePattern('^[0-9a-fA-F]{40}$')] [string] $ArtifactCommit,
    [Parameter(Mandatory = $true)] [ValidatePattern('^0x[0-9a-fA-F]{40}$')] [string] $Executor,
    [Parameter(Mandatory = $true)] [ValidatePattern('^0x[0-9a-fA-F]{40}$')] [string] $Signer,
    [Parameter(Mandatory = $true)] [ValidateNotNullOrEmpty()] [string] $PrivateRelay,
    [Parameter(Mandatory = $true)] [ValidateNotNullOrEmpty()] [string] $Operator,
    [Parameter(Mandatory = $true)] [ValidateNotNullOrEmpty()] [string] $Witness,
    [string] $SessionId
)

$ErrorActionPreference = 'Stop'

# This launcher prepares only a segregated evidence workspace and manifest.
# It never handles private keys, credentials, signing, submission, broadcast,
# or live-capital operations.

$workspacePath = [System.IO.Path]::GetFullPath($Workspace)
New-Item -ItemType Directory -Force -Path $workspacePath | Out-Null

foreach ($lane in @('signer', 'polygon_authority', 'private_relay', 'shadow_staging', 'realized_pnl')) {
    New-Item -ItemType Directory -Force -Path (Join-Path $workspacePath $lane) | Out-Null
}

$args = @(
    'scripts/phase19_gate_console.py',
    $workspacePath,
    '--artifact-commit', $ArtifactCommit.ToLowerInvariant(),
    '--executor', $Executor,
    '--signer', $Signer,
    '--private-relay', $PrivateRelay,
    '--operator', $Operator,
    '--witness', $Witness
)
if ($SessionId) { $args += @('--session-id', $SessionId) }

python @args
if ($LASTEXITCODE -ne 0) { throw "Phase-19 session manifest preparation failed with exit code $LASTEXITCODE" }

Write-Host ""
Write-Host "SESSION WORKSPACE READY: $workspacePath"
Write-Host ""
Write-Host "Next parallel actions:" 
Write-Host "  A  Polygon authority observation -> $workspacePath\polygon_authority\polygon_authority_evidence.json"
Write-Host "  B  External signer challenge/signature -> $workspacePath\signer\signer_evidence.json"
Write-Host "  C  Approved private relay observation -> $workspacePath\private_relay\private_relay_evidence.json"
Write-Host "  D  Identical-artifact shadow/staging -> $workspacePath\shadow_staging\shadow_staging_evidence.json"
Write-Host "  E  Realized settlement evidence remains gated until prerequisites are independently proven"
Write-Host ""
Write-Host "Then run:"
Write-Host "  python scripts/validate_consolidated_evidence_session.py '$workspacePath\session_manifest.json'"
Write-Host ""
Write-Host "Safety: LIVE SIGNING=BLOCKED; PUBLIC BROADCAST=BLOCKED; LIVE CAPITAL=LOCKED"