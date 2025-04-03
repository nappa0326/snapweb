@echo off
REM SnapWeb実行可能ファイルのビルドスクリプト
REM 不要なモジュールを除外し、OpenSSLのDLLを明示的に含めることでサイズを削減

echo SnapWeb実行可能ファイルのビルドを開始します...

REM Anacondaのpythonを使用してPyInstallerを実行
C:\Users\nappa\anaconda3\python.exe -m PyInstaller ^
--onefile ^
--add-binary "C:\Users\nappa\anaconda3\Library\bin\libssl-3-x64.dll;." ^
--add-binary "C:\Users\nappa\anaconda3\Library\bin\libcrypto-3-x64.dll;." ^
--exclude-module matplotlib ^
--exclude-module PyQt5 ^
--exclude-module tkinter ^
--exclude-module numpy ^
--exclude-module pandas ^
--exclude-module scipy ^
snapweb.py

echo ビルドが完了しました。実行可能ファイルは dist\snapweb.exe にあります。