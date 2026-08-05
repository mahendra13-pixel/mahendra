Set WshShell = CreateObject("WScript.Shell")
projectPath = "C:\Users\GIH\Documents\Farwest-Freelance & InfoTech\ff-infotech"
command = "cd /d "" & projectPath & "" && py serve.py"
WshShell.Run command, 0, False
