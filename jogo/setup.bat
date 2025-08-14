@echo off
REM Arquivo .bat para executar o jogo Batalha de Dados
REM Certifique-se de que o Python está instalado no sistema

title Batalha de Dados - Executar Jogo

echo ========================================
echo    BATALHA DE DADOS - INICIALIZADOR
echo ========================================
echo.

REM Verificar se o Python está disponível
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: Python nao encontrado no sistema!
    echo Por favor, instale o Python 3.x primeiro.
    echo.
    pause
    exit /b 1
)

REM Verificar se o arquivo script.py existe
if not exist "script.py" (
    echo ERRO: Arquivo script.py nao encontrado!
    echo Certifique-se de que o script.py esta na mesma pasta.
    echo.
    pause
    exit /b 1
)

echo Verificando dependencias...
echo.

REM Instalar colorama se necessário
pip show colorama >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalando colorama...
    pip install colorama
    echo.
)

echo Iniciando Batalha de Dados...
echo.
echo ----------------------------------------

REM Executar o jogo
python script.py

echo ----------------------------------------
echo.
echo Jogo finalizado.
echo Obrigado por jogar!

pause