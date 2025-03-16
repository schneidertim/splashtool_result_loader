@echo off
setlocal

:: Set the output zip file name
set ZIPFILE=%USERPROFILE%\Downloads\splashtool_result_loader.zip

:: Remove existing zip file if it exists
if exist %ZIPFILE% del %ZIPFILE%

:: Create the zip file directly from the splashtool_result_loader directory
powershell Compress-Archive -Path "splashtool_result_loader\*" -DestinationPath %ZIPFILE%

echo Plugin zip file created successfully: %ZIPFILE% 