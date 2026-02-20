Set WshShell = CreateObject("WScript.Shell")
' Sửa lại đường dẫn tới file .bat của bạn
WshShell.Run chr(34) & "D:\Python\realtime_estimate_tracker\run_pipeline.bat" & Chr(34), 0
Set WshShell = Nothing