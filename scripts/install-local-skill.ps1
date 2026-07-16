# Wrapper for cross-platform skill linking on Windows.
param(
    [Parameter(Mandatory = $true)]
    [string]$Target,

    [Parameter(Mandatory = $false)]
    [string]$SkillName,

    [Parameter(Mandatory = $false)]
    [ValidateSet("codex", "cursor", "kimi", "claude")]
    [string]$Agent,

    [switch]$Force,
    [switch]$DryRun
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$linkScript = Join-Path $scriptDir "link-skills.py"

$args = @("--target", $Target)
if ($SkillName) {
    $args += @("--skill", $SkillName)
}
if ($Agent) {
    $args += @("--agent", $Agent)
}
if ($Force) {
    $args += "--force"
}
if ($DryRun) {
    $args += "--dry-run"
}

python $linkScript @args
exit $LASTEXITCODE
