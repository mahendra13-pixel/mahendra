Set WshShell = CreateObject("WScript.Shell")
projectPath = "C:\Users\GIH\Documents\Farwest-Freelance & InfoTech\ff-infotech"
pyPath = "C:\Users\GIH\AppData\Local\Programs\Python\Launcher\py.exe"
WshShell.Run "cmd /c for /f ""tokens=5"" %a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %a", 0, True
WScript.Sleep 1000
WshShell.Run "cmd /c cd /d "" & projectPath & "" && "" & pyPath & "" serve.py", 0, False
WScript.Sleep 3000
Set objExec = WshShell.Exec("cmd /c netstat -ano | findstr :8000 | findstr LISTENING")
If objExec.StdOut.AtEndOfStream Then
    WshShell.Popup "❌ Server failed to start!", 3, "Error", 48
Else
    WshShell.Popup "✅ Django Server started!" & vbCrLf & vbCrLf & "Access at: http://127.0.0.1:8000" & vbCrLf & "Access at: http://172.31.100.19:8000", 4, "Server Started", 64
End If
