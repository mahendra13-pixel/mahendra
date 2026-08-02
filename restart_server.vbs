Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
projectPath = "C:\Users\GIH\Documents\Farwest-Freelance & InfoTech\ff-infotech"

On Error Resume Next
shortPath = fso.GetFolder(projectPath).ShortPath
If Err.Number <> 0 Then shortPath = projectPath
On Error GoTo 0

' Kill existing server
WshShell.Run "cmd /c for /f ""tokens=5"" %a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %a", 0, True
WScript.Sleep 3000

' Start server again
command = "cmd /c cd /d " & Chr(34) & shortPath & Chr(34) & " && py serve.py"
WshShell.Run command, 0, False
WScript.Sleep 2000
WshShell.Popup "🔄 Server Restarted!", 2, "Restarted", 64
