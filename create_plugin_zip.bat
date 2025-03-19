@echo off
setlocal

:: Set the output zip file name
set ZIPFILE=%USERPROFILE%\Downloads\splashtool_result_loader.zip

:: Remove existing zip file if it exists
if exist %ZIPFILE% del %ZIPFILE%

:: Check if 7-Zip exists in the default installation path
set "SEVENZIP=C:\Program Files\7-Zip\7z.exe"
if not exist "%SEVENZIP%" (
    echo Error: 7-Zip not found at %SEVENZIP%
    echo Please install 7-Zip or update the path in the script.
    exit /b 1
)

:: Create the zip file including the parent directory
"%SEVENZIP%" a -tzip "%ZIPFILE%" "splashtool_result_loader"

echo Plugin zip file created successfully: %ZIPFILE%