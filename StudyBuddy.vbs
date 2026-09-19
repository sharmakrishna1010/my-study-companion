Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
strScriptPath = fso.GetParentFolderName(WScript.ScriptFullName)

strPythonw = "pythonw.exe"
If fso.FileExists("C:\Users\Krishna Sharma\AppData\Local\Programs\Python\Python313\pythonw.exe") Then
    strPythonw = """C:\Users\Krishna Sharma\AppData\Local\Programs\Python\Python313\pythonw.exe"""
End If

WshShell.CurrentDirectory = strScriptPath
WshShell.Run strPythonw & " src\app.py", 0, False
