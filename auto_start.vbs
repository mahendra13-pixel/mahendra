Set WshShell = CreateObject("WScript.Shell")
projectPath = "C:\Users\GIH\Documents\Farwest-Freelance & InfoTech\ff-infotech"
pyPath = "C:\Users\GIH\AppData\Local\Programs\Python\Python313\python.exe"
WshShell.Run "cmd /c cd /d "" & projectPath & "" && "" & pyPath & "" serve.py", 0, False
