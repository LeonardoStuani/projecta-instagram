@echo off
rem Atalho para o ig.py com o Python portatil da pasta PLANO. Ex.: ig plano
set PYTHONUTF8=1
"%~dp0..\..\ferramentas\python\python.exe" "%~dp0scripts\ig.py" %*
