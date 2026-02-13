@echo off
setlocal

cd /d c:\Users\Jasmine\Downloads\weather!-20260210T150019Z-1-001\weather!

echo NOTE: This runs against the local database and may differ from Render production.
python manage.py process_alerts

echo.
echo NOTE: This triggers the Render endpoint. Set RENDER_ALERTS_URL and RENDER_ALERTS_TOKEN below.
set "RENDER_ALERTS_URL="
set "RENDER_ALERTS_TOKEN="

if "%RENDER_ALERTS_URL%"=="" (
  echo Skipping Render call: RENDER_ALERTS_URL not set.
  goto :eof
)

if "%RENDER_ALERTS_TOKEN%"=="" (
  echo Skipping Render call: RENDER_ALERTS_TOKEN not set.
  goto :eof
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$headers = @{ 'X-Alert-Token' = '%RENDER_ALERTS_TOKEN%' }; " ^
  "try { " ^
  "  $resp = Invoke-RestMethod -Method Post -Uri '%RENDER_ALERTS_URL%' -Headers $headers; " ^
  "  Write-Host ('Render response: ' + ($resp | ConvertTo-Json -Depth 6)); " ^
  "} catch { " ^
  "  Write-Host ('Render call failed: ' + $_.Exception.Message); " ^
  "  exit 1; " ^
  "}"
  
