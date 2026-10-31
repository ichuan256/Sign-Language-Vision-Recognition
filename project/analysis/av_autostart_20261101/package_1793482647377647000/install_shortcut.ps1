$avShell=New-Object -ComObject WScript.Shell
$avLink=$avShell.CreateShortcut('C:\Users\sunjiayi\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\SignAV三栏自启.lnk')
$avLink.TargetPath='F:\PLD\.venv-vision\Scripts\pythonw.exe'
$avLink.Arguments='-X utf8 "F:\PLD_new\Sign-Language-Vision-Recognition\project\scripts\av_autostart.py"'
$avLink.WorkingDirectory='F:\PLD_new\Sign-Language-Vision-Recognition'
$avLink.WindowStyle=7
$avLink.Save()
if ($avLink.TargetPath -ne 'F:\PLD\.venv-vision\Scripts\pythonw.exe') { throw 'Shortcut target mismatch' }
