' ============================================================
' setup_all.vbs - Complete Django Server Setup
' Run this ONCE as Administrator
' ============================================================

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

projectPath = "C:\Users\GIH\Documents\Farwest-Freelance & InfoTech\ff-infotech"
pyPath = "C:\Users\GIH\AppData\Local\Programs\Python\Python313\python.exe"
pythonPath = "C:\Users\GIH\AppData\Local\Programs\Python\Python313\python.exe"

' ============================================================
' 1. CREATE ALL VBS FILES
' ============================================================

' 1a. auto_start.vbs - Runs on Windows boot
Set file = fso.CreateTextFile(projectPath & "\auto_start.vbs", True)
file.WriteLine "Set WshShell = CreateObject(""WScript.Shell"")"
file.WriteLine "projectPath = """ & projectPath & """"
file.WriteLine "pyPath = """ & pyPath & """"
file.WriteLine "WshShell.Run ""cmd /c cd /d """" & projectPath & """" && """" & pyPath & """" serve.py"", 0, False"
file.Close

' 1b. monitor_server.vbs - Checks every 30 minutes
Set file = fso.CreateTextFile(projectPath & "\monitor_server.vbs", True)
file.WriteLine "Set WshShell = CreateObject(""WScript.Shell"")"
file.WriteLine "Set fso = CreateObject(""Scripting.FileSystemObject"")"
file.WriteLine "projectPath = """ & projectPath & """"
file.WriteLine "pyPath = """ & pyPath & """"
file.WriteLine "logFile = projectPath & ""\server_monitor.log"""
file.WriteLine ""
file.WriteLine "Sub WriteLog(message)"
file.WriteLine "    Dim logStream"
file.WriteLine "    Set logStream = fso.OpenTextFile(logFile, 8, True)"
file.WriteLine "    logStream.WriteLine Now() & "" - "" & message"
file.WriteLine "    logStream.Close"
file.WriteLine "End Sub"
file.WriteLine ""
file.WriteLine "Set objExec = WshShell.Exec(""cmd /c netstat -ano | findstr :8000 | findstr LISTENING"")"
file.WriteLine ""
file.WriteLine "If objExec.StdOut.AtEndOfStream Then"
file.WriteLine "    WriteLog ""Server not running. Attempting to start..."""
file.WriteLine "    WshShell.Run ""cmd /c for /f """"tokens=5"""" %a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %a"", 0, True"
file.WriteLine "    WScript.Sleep 1000"
file.WriteLine "    WshShell.Run ""cmd /c cd /d """" & projectPath & """" && """" & pyPath & """" serve.py"", 0, False"
file.WriteLine "    WScript.Sleep 5000"
file.WriteLine "    Set objExec2 = WshShell.Exec(""cmd /c netstat -ano | findstr :8000 | findstr LISTENING"")"
file.WriteLine "    If objExec2.StdOut.AtEndOfStream Then"
file.WriteLine "        WriteLog ""ERROR: Failed to start server!"""
file.WriteLine "    Else"
file.WriteLine "        WriteLog ""SUCCESS: Server started!"""
file.WriteLine "    End If"
file.WriteLine "End If"
file.Close

' 1c. start_now.vbs - Start manually
Set file = fso.CreateTextFile(projectPath & "\start_now.vbs", True)
file.WriteLine "Set WshShell = CreateObject(""WScript.Shell"")"
file.WriteLine "projectPath = """ & projectPath & """"
file.WriteLine "pyPath = """ & pyPath & """"
file.WriteLine "WshShell.Run ""cmd /c for /f """"tokens=5"""" %a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %a"", 0, True"
file.WriteLine "WScript.Sleep 1000"
file.WriteLine "WshShell.Run ""cmd /c cd /d """" & projectPath & """" && """" & pyPath & """" serve.py"", 0, False"
file.WriteLine "WScript.Sleep 3000"
file.WriteLine "Set objExec = WshShell.Exec(""cmd /c netstat -ano | findstr :8000 | findstr LISTENING"")"
file.WriteLine "If objExec.StdOut.AtEndOfStream Then"
file.WriteLine "    WshShell.Popup ""❌ Server failed to start!"", 3, ""Error"", 48"
file.WriteLine "Else"
file.WriteLine "    WshShell.Popup ""✅ Django Server started!"" & vbCrLf & vbCrLf & ""Access at: http://127.0.0.1:8000"" & vbCrLf & ""Access at: http://172.31.100.19:8000"", 4, ""Server Started"", 64"
file.WriteLine "End If"
file.Close

' 1d. stop_now.vbs - Stop manually
Set file = fso.CreateTextFile(projectPath & "\stop_now.vbs", True)
file.WriteLine "Set WshShell = CreateObject(""WScript.Shell"")"
file.WriteLine "WshShell.Run ""cmd /c for /f """"tokens=5"""" %a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %a"", 0, False"
file.WriteLine "WScript.Sleep 1000"
file.WriteLine "WshShell.Popup ""✅ Django Server stopped!"", 2, ""Server Stopped"", 64"
file.Close

' 1e. check_status.vbs - Check if running
Set file = fso.CreateTextFile(projectPath & "\check_status.vbs", True)
file.WriteLine "Set WshShell = CreateObject(""WScript.Shell"")"
file.WriteLine "Set objExec = WshShell.Exec(""cmd /c netstat -ano | findstr :8000 | findstr LISTENING"")"
file.WriteLine "If objExec.StdOut.AtEndOfStream Then"
file.WriteLine "    WshShell.Popup ""❌ Django Server is NOT running!"", 3, ""Server Status"", 48"
file.WriteLine "Else"
file.WriteLine "    WshShell.Popup ""✅ Django Server is RUNNING!"", 3, ""Server Status"", 64"
file.WriteLine "End If"
file.Close

' 1f. restart_now.vbs - Restart
Set file = fso.CreateTextFile(projectPath & "\restart_now.vbs", True)
file.WriteLine "Set WshShell = CreateObject(""WScript.Shell"")"
file.WriteLine "projectPath = """ & projectPath & """"
file.WriteLine "pyPath = """ & pyPath & """"
file.WriteLine "WshShell.Run ""cmd /c for /f """"tokens=5"""" %a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %a"", 0, True"
file.WriteLine "WScript.Sleep 2000"
file.WriteLine "WshShell.Run ""cmd /c cd /d """" & projectPath & """" && """" & pyPath & """" serve.py"", 0, False"
file.WriteLine "WScript.Sleep 3000"
file.WriteLine "WshShell.Popup ""✅ Django Server restarted!"", 3, ""Server Restarted"", 64"
file.Close

' ============================================================
' 2. ADD TO WINDOWS STARTUP
' ============================================================

startupFolder = WshShell.SpecialFolders("Startup")
Set oShellLink = WshShell.CreateShortcut(startupFolder & "\Django Server.lnk")
oShellLink.TargetPath = "wscript.exe"
oShellLink.Arguments = """" & projectPath & "\auto_start.vbs"""
oShellLink.WorkingDirectory = projectPath
oShellLink.Description = "Django Web Server"
oShellLink.WindowStyle = 7
oShellLink.IconLocation = "shell32.dll, 14"
oShellLink.Save

' ============================================================
' 3. CREATE TASK SCHEDULER TASK (Runs every 30 minutes)
' ============================================================

taskName = "DjangoServerMonitor"
monitorPath = projectPath & "\monitor_server.vbs"

' Delete existing task
WshShell.Run "schtasks /delete /tn """ & taskName & """ /f", 0, True

' Create new task
createTaskCmd = "schtasks /create /tn """ & taskName & """ " & _
    "/tr ""wscript.exe """ & monitorPath & """"" " & _
    "/sc minute /mo 30 " & _
    "/ru SYSTEM /rl HIGHEST " & _
    "/f"
WshShell.Run createTaskCmd, 0, True

' ============================================================
' 4. ADD FIREWALL RULE
' ============================================================

WshShell.Run "netsh advfirewall firewall add rule name=""Django Server"" dir=in action=allow protocol=TCP localport=8000", 0, True

' ============================================================
' 5. START SERVER NOW
' ============================================================

' Kill existing
WshShell.Run "cmd /c for /f ""tokens=5"" %a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %a", 0, True
WScript.Sleep 1000

' Start server
WshShell.Run "cmd /c cd /d """ & projectPath & """ && """ & pyPath & """ serve.py", 0, False

WScript.Sleep 3000

' ============================================================
' 6. SHOW COMPLETION
' ============================================================

' Check if running
Set objExec = WshShell.Exec("cmd /c netstat -ano | findstr :8000 | findstr LISTENING")

If objExec.StdOut.AtEndOfStream Then
    status = "❌ Server NOT running! Check manually."
Else
    status = "✅ Server IS running!"
End If

WshShell.Popup "✅ Setup Complete!" & vbCrLf & vbCrLf & _
    "📂 Files created in:" & vbCrLf & projectPath & vbCrLf & vbCrLf & _
    "   auto_start.vbs - Starts on boot" & vbCrLf & _
    "   monitor_server.vbs - Checks every 30 min" & vbCrLf & _
    "   start_now.vbs - Start manually" & vbCrLf & _
    "   stop_now.vbs - Stop manually" & vbCrLf & _
    "   check_status.vbs - Check if running" & vbCrLf & _
    "   restart_now.vbs - Restart manually" & vbCrLf & vbCrLf & _
    "🔄 Task Scheduler: " & taskName & " (every 30 min)" & vbCrLf & _
    "🛡️ Firewall: Port 8000 allowed" & vbCrLf & _
    "🚀 Status: " & status & vbCrLf & vbCrLf & _
    "🌐 Access at: http://127.0.0.1:8000" & vbCrLf & _
    "🌐 Access at: http://172.31.100.19:8000", 15, "Installation Complete", 64