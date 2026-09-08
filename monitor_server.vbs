Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
projectPath = "C:\Users\GIH\Documents\Farwest-Freelance & InfoTech\ff-infotech"
pyPath = "C:\Users\GIH\AppData\Local\Programs\Python\Python313\python.exe"
logFile = projectPath & "\server_monitor.log"

Sub WriteLog(message)
    Dim logStream
    Set logStream = fso.OpenTextFile(logFile, 8, True)
    logStream.WriteLine Now() & " - " & message
    logStream.Close
End Sub

Set objExec = WshShell.Exec("cmd /c netstat -ano | findstr :8000 | findstr LISTENING")

If objExec.StdOut.AtEndOfStream Then
    WriteLog "Server not running. Attempting to start..."
    WshShell.Run "cmd /c for /f ""tokens=5"" %a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %a", 0, True
    WScript.Sleep 1000
    WshShell.Run "cmd /c cd /d "" & projectPath & "" && "" & pyPath & "" serve.py", 0, False
    WScript.Sleep 5000
    Set objExec2 = WshShell.Exec("cmd /c netstat -ano | findstr :8000 | findstr LISTENING")
    If objExec2.StdOut.AtEndOfStream Then
        WriteLog "ERROR: Failed to start server!"
    Else
        WriteLog "SUCCESS: Server started!"
    End If
End If
