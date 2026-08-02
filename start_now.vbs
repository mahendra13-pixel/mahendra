Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
projectPath = "C:\Users\GIH\Documents\Farwest-Freelance & InfoTech\ff-infotech"

On Error Resume Next
shortPath = fso.GetFolder(projectPath).ShortPath
If Err.Number <> 0 Then shortPath = projectPath
On Error GoTo 0

command = "cmd /c cd /d " & Chr(34) & shortPath & Chr(34) & " && py serve.py"
WshShell.Run command, 0, False
WScript.Sleep 2000
WshShell.Popup "✅ Django Server started!", 2, "Server Started", 64
