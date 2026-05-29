$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$runFolder = "run_insurance_name_truncation_$timestamp"
$runPath = Join-Path $PWD $runFolder

Write-Host "=== Creating output folder: $runFolder ==="
New-Item -ItemType Directory -Path $runPath -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $runPath "tmp") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $runPath "tests") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $runPath "allure-report") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $runPath "allure-results") -Force | Out-Null

# Clean previous run artifacts
Remove-Item -Recurse -Force ".tmp" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "generated_test_cases.md" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "playwright-results.json" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "tests" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "allure-report" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "allure-results" -ErrorAction SilentlyContinue

# Set env vars for DME Rocket
$env:TARGET_APP_URL = "https://dev.dmerocket.com/insurance"
$env:USERNAME = "admin@selectortho.net"  
$env:PASSWORD = "Password123!"

Write-Host ""
Write-Host "=== Running pipeline with DME Rocket Insurance Name Truncation retest ==="
Write-Host "Target URL: $env:TARGET_APP_URL"
Write-Host "Output will be saved to: $runPath"
Write-Host ""

python main.py --document "BUG_Retest_Insurance_Name_Truncation.md" --regression 2>&1

Write-Host ""
Write-Host "=== Copying outputs to: $runFolder ==="

# Copy context
if (Test-Path ".tmp/context.json") {
    Copy-Item ".tmp/context.json" (Join-Path $runPath "tmp/context.json") -Force
}
# Copy generated test cases
if (Test-Path "generated_test_cases.md") {
    Copy-Item "generated_test_cases.md" (Join-Path $runPath "generated_test_cases.md") -Force
}
# Copy playwright results
if (Test-Path "playwright-results.json") {
    Copy-Item "playwright-results.json" (Join-Path $runPath "playwright-results.json") -Force
}
# Copy deep evaluation report
if (Test-Path "deep_evaluation_report.html") {
    Copy-Item "deep_evaluation_report.html" (Join-Path $runPath "deep_evaluation_report.html") -Force
}
# Copy test specs
if (Test-Path "tests/specs") {
    Copy-Item -Recurse "tests/specs" (Join-Path $runPath "tests/specs") -Force
}
# Copy page objects
if (Test-Path "tests/pages") {
    Copy-Item -Recurse "tests/pages" (Join-Path $runPath "tests/pages") -Force
}
# Copy allure report
if (Test-Path "allure-report") {
    Copy-Item -Recurse "allure-report/*" (Join-Path $runPath "allure-report") -Force
}
# Copy allure results
if (Test-Path "allure-results") {
    Copy-Item -Recurse "allure-results/*" (Join-Path $runPath "allure-results") -Force
}

Write-Host ""
Write-Host "============================================"
Write-Host "RUN COMPLETE - Results saved to:"
Write-Host "  $runPath"
Write-Host "============================================"
