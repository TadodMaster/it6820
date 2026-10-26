# Runs the per-module test vectors headless.
#   powershell -File tests\run_tests.ps1 [path\to\file.circ]
param([string]$Circ)
$root = Split-Path $PSScriptRoot -Parent
$jar  = Join-Path $root 'logisim-evolution-4.1.0-all.jar'
if (-not $Circ) { $Circ = Join-Path $root 'RiscVComputer.circ' }
$java = 'java'
$tests = @(
  @{ circuit = 'ALU';            vec = 'alu.vec' },
  @{ circuit = 'ALUControl';     vec = 'alucontrol.vec' },
  @{ circuit = 'MainControl';    vec = 'maincontrol.vec' },
  @{ circuit = 'ImmGen';         vec = 'immgen.vec' },
  @{ circuit = 'BranchUnit';     vec = 'branchunit.vec' },
  @{ circuit = 'ForwardingUnit'; vec = 'forwardingunit.vec' },
  @{ circuit = 'HazardUnit';     vec = 'hazardunit.vec' },
  @{ circuit = 'LoadExtract';    vec = 'loadextract.vec' },
  @{ circuit = 'StoreMerge';     vec = 'storemerge.vec' }
)
$fail = 0
foreach ($t in $tests) {
  $out = & $java -jar $jar --test-vector $t.circuit (Join-Path $PSScriptRoot $t.vec) $Circ 2>&1 | Out-String
  $m = [regex]::Match($out, 'Passed: (\d+), Failed: (\d+)')
  $line = if ($m.Success) { "passed $($m.Groups[1].Value), failed $($m.Groups[2].Value)" } else { "no result:`n$out" }
  "{0,-15} {1}" -f $t.circuit, $line
  if (-not $m.Success -or $m.Groups[2].Value -ne '0') { $fail++; $out }
}
if ($fail) { "FAILED: $fail module(s)"; exit 1 } else { 'ALL PASSED' }