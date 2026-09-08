Set WshShell = CreateObject("WScript.Shell")
projectPath = "C:\Users\GIH\Documents\Farwest-Freelance & InfoTech\ff-infotech"
pyPath = "C:\Users\GIH\AppData\Local\Programs\Python\Python313\python.exe"
WshShell.Run "cmd /c for /f ""tokens=5"" %a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %a", 0, True
WScript.Sleep 2000
WshShell.Run "cmd /c cd /d "" & projectPath & "" && "" & pyPath & "" serve.py", 0, False
WScript.Sleep 3000
WshShell.Popup "✅ Django Server restarted!", 3, "Server Restarted", 64
