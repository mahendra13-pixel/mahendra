Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
projectPath = "C:\Users\GIH\Documents\Farwest-Freelance & InfoTech\ff-infotech"

' Use short path to handle spaces and &
On Error Resume Next
shortPath = fso.GetFolder(projectPath).ShortPath
If Err.Number <> 0 Then
    shortPath = projectPath
End If
On Error GoTo 0

' Wait for network to be ready
WScript.Sleep 30000

' Start server hidden
command = "cmd /c cd /d " & Chr(34) & shortPath & Chr(34) & " && py serve.py"
WshShell.Run command, 0, False

' Log startup
logFile = projectPath & "\server_monitor.log"
On Error Resume Next
Set logStream = fso.OpenTextFile(logFile, 8, True)
If Err.Number = 0 Then
    logStream.WriteLine Now() & " - SERVER STARTED VIA STARTUP"
    logStream.Close
End If
On Error GoTo 0
