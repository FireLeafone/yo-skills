# Wrapper for cross-platform skill linking on Windows.
param(
    [Parameter(Mandatory = $true)]
    [string]$Target,

    [Parameter(Mandatory = $false)]
    [string]$SkillName,

    [switch]$Force,
    [switch]$DryRun
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$linkScript = Join-Path $scriptDir "link-skills.py"

$args = @("--target", $Target)
if ($SkillName) {
    $args += @("--skill", $SkillName)
}
if ($Force) {
    $args += "--force"
}
if ($DryRun) {
    $args += "--dry-run"
}

python $linkScript @args
exit $LASTEXITCODE
