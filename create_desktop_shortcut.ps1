$PythonwPath = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
if (-not $PythonwPath) {
    $PythonwPath = "C:\Users\Krishna Sharma\AppData\Local\Programs\Python\Python313\pythonw.exe"
}

$ScriptDir = $PSScriptRoot
$AppPyPath = Join-Path -Path $ScriptDir -ChildPath "src\app.py"
$ExePath = Join-Path -Path $ScriptDir -ChildPath "dist\StudyBuddy\StudyBuddy.exe"

# Target standalone executable if built, otherwise fallback to pythonw
if (Test-Path $ExePath) {
    $TargetPath = $ExePath
    $Arguments = ""
    $WorkingDir = Join-Path -Path $ScriptDir -ChildPath "dist\StudyBuddy"
    $IconLocation = "$ExePath,0"
} else {
    $TargetPath = $PythonwPath
    $Arguments = "`"$AppPyPath`""
    $WorkingDir = $ScriptDir
    $IconLocation = ""
}

$DesktopPath = [System.Environment]::GetFolderPath("Desktop")
$StartMenuPath = [System.Environment]::GetFolderPath("Programs")

$Locations = @(
    @{ Name = "Desktop"; Path = Join-Path -Path $DesktopPath -ChildPath "Study Buddy.lnk" },
    @{ Name = "Start Menu"; Path = Join-Path -Path $StartMenuPath -ChildPath "Study Buddy.lnk" }
)

$WshShell = New-Object -ComObject WScript.Shell

foreach ($Loc in $Locations) {
    $Shortcut = $WshShell.CreateShortcut($Loc.Path)
    $Shortcut.TargetPath = $TargetPath
    if ($Arguments) { $Shortcut.Arguments = $Arguments }
    $Shortcut.WorkingDirectory = $WorkingDir
    $Shortcut.Description = "Study Companion AI Desktop Pet"
    if ($IconLocation) { $Shortcut.IconLocation = $IconLocation }
    $Shortcut.Save()
    Write-Host "Created $($Loc.Name) shortcut at: $($Loc.Path)"
}
