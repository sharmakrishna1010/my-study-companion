Write-Host "Building StudyBuddy executable with PyInstaller..."
pyinstaller --noconsole --noconfirm --name "StudyBuddy" --add-data "assets;assets" src/app.py

if ($LASTEXITCODE -eq 0) {
    Copy-Item -Path ".env" -Destination "dist\StudyBuddy\.env" -Force
    Write-Host "Executable built successfully in dist\StudyBuddy\StudyBuddy.exe"
    
    Write-Host "Creating Desktop and Start Menu shortcuts..."
    & "$PSScriptRoot\create_desktop_shortcut.ps1"
} else {
    Write-Error "PyInstaller build failed."
}
