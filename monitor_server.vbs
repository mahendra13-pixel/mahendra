Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
projectPath = "C:\Users\GIH\Documents\Farwest-Freelance & InfoTech\ff-infotech"
logFile = projectPath & "\server_monitor.log"

' Get short path to avoid spaces & special chars
On Error Resume Next
shortPath = fso.GetFolder(projectPath).ShortPath
If Err.Number <> 0 Then
    shortPath = projectPath
End If
On Error GoTo 0

Sub WriteLog(message)
    On Error Resume Next
    Set logStream = fso.OpenTextFile(logFile, 8, True)
    If Err.Number = 0 Then
        logStream.WriteLine Now() & " - " & message
        logStream.Close
    End If
    On Error GoTo 0
End Sub

Sub StartServer()
    WriteLog "Server not running. Starting..."
    command = "cmd /c cd /d " & Chr(34) & shortPath & Chr(34) & " && py serve.py"
    WshShell.Run command, 0, False
    WScript.Sleep 10000
    Set objCheck = WshShell.Exec("cmd /c netstat -ano | findstr :8000 | findstr LISTENING")
    If objCheck.StdOut.AtEndOfStream Then
        WriteLog "ERROR: Failed to start server!"
    Else
        WriteLog "SUCCESS: Server started!"
    End If
End Sub

WriteLog "=== CHECKING SERVER STATUS ==="
Set objExec = WshShell.Exec("cmd /c netstat -ano | findstr :8000 | findstr LISTENING")

If objExec.StdOut.AtEndOfStream Then
    StartServer()
Else
    WriteLog "Server is running. No action needed."
End If
