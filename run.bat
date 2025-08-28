@echo off
REM FlowDesk 应用程序启动脚本 - Windows批处理版本
REM 自动处理路径问题，简化启动流程

echo 启动 FlowDesk 应用程序...
cd /d "%~dp0"
python src\flowdesk\app.py
pause
