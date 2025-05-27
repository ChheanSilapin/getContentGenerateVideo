# PowerShell script to create installer package
$version = "0.0.3"
$distPath = "dist"
$installerName = "Video_Generator_Setup_$version.exe"

Write-Host "Creating installer package for Video Generator v$version"

# Create portable version directory
$portableDir = "$distPath\Video_Generator_Portable_v$version"
if (Test-Path $portableDir) {
    Remove-Item $portableDir -Recurse -Force
}
New-Item -ItemType Directory -Path $portableDir -Force

# Copy executable and FFmpeg files
Copy-Item "$distPath\Video Generator.exe" "$portableDir\" -Force
Copy-Item "ffmpeg.exe" "$portableDir\" -Force -ErrorAction SilentlyContinue
Copy-Item "ffplay.exe" "$portableDir\" -Force -ErrorAction SilentlyContinue
Copy-Item "ffprobe.exe" "$portableDir\" -Force -ErrorAction SilentlyContinue

# Create README
@"
Video Generator v$version (Portable)
====================================

SUBTITLE FIX INCLUDED
This version fixes the subtitle embedding issue on Windows systems.

Installation:
1. Extract all files to a folder
2. Run "Video Generator.exe"

Features:
- Generate videos from text and images
- Add subtitles automatically
- Multiple aspect ratios (9:16, 16:9, 1:1)
- Voice synthesis
- Video effects and enhancements

Requirements:
- Windows 10 or later
- No additional software required (all dependencies included)

Version $version Changes:
- Fixed FFmpeg subtitle embedding on Windows
- Improved path handling for Windows systems
- Enhanced compatibility with different Windows configurations

Support:
If you encounter any issues, please report them with details about your system.
"@ | Out-File -FilePath "$portableDir\README.txt" -Encoding UTF8

# Create run script
@"
@echo off
echo Starting Video Generator...
"Video Generator.exe"
pause
"@ | Out-File -FilePath "$portableDir\Run_Video_Generator.bat" -Encoding ASCII

# Create ZIP file
$zipPath = "$distPath\Video_Generator_Portable_v$version.zip"
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

Write-Host "Creating ZIP file: $zipPath"
Compress-Archive -Path "$portableDir\*" -DestinationPath $zipPath -Force

Write-Host "Portable version created successfully: $zipPath"
Write-Host "Files included:"
Get-ChildItem $portableDir | ForEach-Object { Write-Host "  - $($_.Name)" }
