@echo off
set output=results.txt

echo. > "%output%"

for /R %%f in (*.rpy) do (
    findstr /C:"checklistappend(" "%%f" > temp.txt
    if not errorlevel 1 (
        echo ===== %%f ===== >> "%output%"
        type temp.txt >> "%output%"
        echo. >> "%output%"
    )
)

del temp.txt

echo Done! Results saved to %output%
pause