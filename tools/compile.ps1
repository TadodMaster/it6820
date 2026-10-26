# Compile the Java helpers (test runner, circuit renderer, pin-position dump) into tools\bin.
# Needs a JDK 21 (javac).   usage: powershell -File tools\compile.ps1
$root = Split-Path $PSScriptRoot -Parent
$jar  = Join-Path $root 'logisim-evolution-4.1.0-all.jar'
New-Item -ItemType Directory -Force (Join-Path $PSScriptRoot 'bin') | Out-Null
& javac -cp $jar -d (Join-Path $PSScriptRoot 'bin') (Get-ChildItem (Join-Path $PSScriptRoot 'java') -Filter *.java).FullName
if ($LASTEXITCODE -eq 0) { 'compiled to tools\bin' }
