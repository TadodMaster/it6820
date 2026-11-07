# Pre-flight check before the presentation: run it 15 minutes before and once more right before you start.
#   powershell -ExecutionPolicy Bypass -File tools\presentation_check.ps1 [-Quick]
# -Quick skips the random-program test. Takes about 1.5 minutes (30 s with -Quick).
param([switch]$Quick)
$ErrorActionPreference = 'Continue'
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root
$results = @()
function Step($name, [scriptblock]$body) {
    $t = Get-Date
    try { $r = & $body; $ok = [bool]$r.Ok; $note = $r.Note } catch { $ok = $false; $note = $_.Exception.Message }
    $sec = [int]((Get-Date) - $t).TotalSeconds
    $tag = if ($ok) { 'PASS' } else { 'FAIL' }
    $color = if ($ok) { 'Green' } else { 'Red' }
    Write-Host ("[{0}] {1,-46} {2,3}s  {3}" -f $tag, $name, $sec, $note) -ForegroundColor $color
    $script:results += $ok
}

# --- Java 21
$java = $null
foreach ($c in @($env:JAVA, 'java', (Get-ChildItem 'C:\Program Files\Java\jdk-21*\bin\java.exe' -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName))) {
    if (-not $c) { continue }
    try {
        $v = (& $c -version 2>&1 | Select-Object -First 1).ToString()
        if ($v -match '"(\d+)') { if ([int]$Matches[1] -ge 21) { $java = $c; break } }
    } catch { }
}
Step 'Java 21 or newer' { @{ Ok = [bool]$java; Note = $(if ($java) { "$java" } else { 'not found: install JDK 21 (see commands.txt)' }) } }
if (-not $java) { Write-Host 'Cannot continue without Java 21.' -ForegroundColor Red; exit 1 }
$env:JAVA = $java
$env:Path = (Split-Path $java) + ';' + $env:Path

Step 'Project files present' {
    $need = 'RiscVComputer.circ', 'logisim-evolution-4.1.0-all.jar', 'programs\demo.hex', 'programs\hazards_demo.hex', 'tools\bin\Run.class', 'tools\rv.py'
    $missing = $need | Where-Object { -not (Test-Path (Join-Path $root $_)) }
    @{ Ok = ($missing.Count -eq 0); Note = $(if ($missing) { 'missing: ' + ($missing -join ', ') } else { 'all there' }) }
}

Step 'ROM of both CPUs holds programs\demo.s' {
    $out = python -c @"
import re, sys
t = open('RiscVComputer.circ', encoding='utf-8').read()
want = [w.strip() for w in open('programs/demo.hex').read().split()[2:]]
res = []
for c in ('main', 'Pipeline'):
    b = re.search(r'  <circuit name=\"%s\">.*?</circuit>' % c, t, re.S).group(0)
    rom = re.search(r'name=\"ROM\">.*?<a name=\"contents\">(.*?)</a>', b, re.S).group(1).split()[3:]
    res.append(rom[:len(want)] == want)
print('OK' if all(res) else 'DIFFERENT')
"@
    @{ Ok = ($out -match 'OK'); Note = $(if ($out -match 'OK') { 'main and Pipeline: 13 words match' } else { 'ROM differs from demo.hex: rebuild or reload the program' }) }
}

Step 'Module tests (9 files, Logisim test vectors)' {
    $o = powershell -NoProfile -File tests\run_tests.ps1 2>&1 | Out-String
    @{ Ok = ($o -match 'ALL PASSED'); Note = $(if ($o -match 'ALL PASSED') { '106 test rows pass' } else { 'see: powershell -File tests\run_tests.ps1' }) }
}

Step 'Programs on both CPUs vs reference simulator' {
    $o = python tests\run_cpu_tests.py --circuit all 2>&1 | Out-String
    @{ Ok = ($o -match 'ALL PASSED'); Note = $(if ($o -match 'ALL PASSED') { '7 programs x 2 CPUs match' } else { 'see: python tests\run_cpu_tests.py --circuit all' }) }
}

if (-not $Quick) {
    Step 'Random programs on both CPUs (6 programs)' {
        $o = python tests\fuzz.py --count 6 --seed 777 2>&1 | Out-String
        @{ Ok = ($o -match 'ALL PASSED'); Note = $(if ($o -match 'ALL PASSED') { '12 runs match' } else { 'see: python tests\fuzz.py' }) }
    }
}

Step 'Live proof (the screen you will show)' {
    $o = python tools\live_proof.py --no-color 2>&1 | Out-String
    @{ Ok = ($o -match 'VERDICT: both CPUs produce exactly'); Note = 'verdict line found' }
}

Write-Host ''
if ($results -notcontains $false) {
    Write-Host 'READY: everything passed.' -ForegroundColor Green
    Write-Host 'Before you start: close other Logisim windows, close chat / mail apps (notifications pop up over the screen), then follow docs\PRESENTATION.md.'
} else {
    Write-Host 'NOT READY: fix the FAIL lines first (docs\PRESENTATION.md, section "If something goes wrong").' -ForegroundColor Red
    exit 1
}
