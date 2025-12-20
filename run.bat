@echo off
:: Enter project folder if we're outside
if exist "getContentGenerateVideo" cd getContentGenerateVideo

echo Starting Video Generator...
uv run main.py
