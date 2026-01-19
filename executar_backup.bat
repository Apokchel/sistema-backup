@echo off
echo ========================================
echo Sistema de Backup MongoDB
echo ========================================
echo.

REM Verifica se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Por favor, instale o Python e adicione ao PATH.
    pause
    exit /b 1
)

REM Instala dependências se necessário
echo Verificando dependencias...
pip show pymongo >nul 2>&1
if errorlevel 1 (
    echo Instalando dependencias...
    pip install -r requirements.txt
)

echo.
echo Executando backup...
echo.

REM Executa o script Python
python backup_mongodb.py

echo.
pause

