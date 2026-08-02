Set WshShell = CreateObject("WScript.Shell")
Set objExec = WshShell.Exec("cmd /c netstat -ano | findstr :8000 | findstr LISTENING")
If objExec.StdOut.AtEndOfStream Then
    WshShell.Popup "❌ Django Server is NOT running!", 3, "Server Status", 48
Else
    WshShell.Popup "✅ Django Server is RUNNING!", 3, "Server Status", 64
End If
