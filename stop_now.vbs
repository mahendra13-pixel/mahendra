Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c for /f ""tokens=5"" %a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %a", 0, False
WScript.Sleep 1000
WshShell.Popup "✅ Django Server stopped!", 2, "Server Stopped", 64
