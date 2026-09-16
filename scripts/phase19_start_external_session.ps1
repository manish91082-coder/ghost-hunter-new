$ErrorActionPreference = 'Stop'

param(
    [Parameter(Mandatory = $true)] [string]$Workspace,
    [Parameter(Mandatory = $true)] [string]$ArtifactCommit,
    [Parameter(Mandatory = $true)] [string]$Executor,
    [Parameter(Mandatory = $true)] [string]$Signer,
    [Parameter(Mandatory = $true)] [string]$PrivateRelay,
    [Parameter(Mandatory = $true)] [string]$Operator,
    [Parameter(Mandatory = $true)] [string]$Witness,
    [string]$SessionId
)

Write-Host "PHANTOMX Phase-19 external session bootstrap"
Write-Host "Artifact: $ArtifactCommit"
Write-Host "Safety: no private keys, credentials, raw signed transactions, secrets, broadcast, or live capital."

New-Item -ItemType Directory -Force -Path $Workspace | Out-Null

$arguments = @(
    "scripts/phase19_gate_console.py",
    $Workspace,
    "--artifact-commit", $ArtifactCommit,
    "--executor", $Executor,
    "--signer", $Signer,
    "--private-relay", $PrivateRelay,
    "--operator", $Operator,
    "--witness", $Witness
)
if ($SessionId) {
    $arguments += @("--session-id", $SessionId)
}

python @arguments

Write-Host ""
Write-Host "Next parallel lanes:"
Write-Host "  B Signer: generate fresh challenge; obtain one external signature; verify; store non-secret evidence only."
Write-Host "  A Polygon: capture fresh read-only authority evidence from explicitly approved HTTPS providers."
Write-Host "  C Relay: capture a controlled observation from the explicitly approved private relay."
Write-Host "  D Staging: record identical-artifact non-live execution evidence."
Write-Host ""
Write-Host "Consolidate later with:"
Write-Host "  python scripts/validate_consolidated_evidence_session.py `""$Workspace/session_manifest.json`"""
