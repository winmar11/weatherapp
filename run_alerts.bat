@echo off
cd /d c:\Users\Jasmine\Downloads\weather!-20260210T150019Z-1-001\weather!
echo NOTE: This runs against the local database and may differ from Render production.
python manage.py process_alerts
  
