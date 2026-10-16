@echo off
chcp 65001 >nul
title Face Safety 3.0 - Inicializador Automatico
color 0B

:: ============================================================================
:: FACE SAFETY 3.0 - SCRIPT AUTOMATICO DE INICIALIZACAO E INSTALACAO (.BAT)
:: Criado por Davi Castro (Davicjc) - https://github.com/Davicjc
::
:: Este arquivo facilita o uso do Face Safety no Windows.
:: Voce pode escolher entre:
::   [1] Abrir direto o executavel (.exe) sem precisar instalar nada
::   [2] Instalar automaticamente o opencv-python (se faltar) e rodar o .py
::       (ideal para quem editou a funcao KEY no final do facesafety.py)
::   [3] Criar um ambiente virtual isolado (venv), instalar tudo e abrir
::   [4] Abrir o codigo-fonte (facesafety.py) no Bloco de Notas para editar a KEY
:: ============================================================================

cd /d "%~dp0"

:MENU
cls
echo ============================================================================
echo                     FACE SAFETY 3.0 - MENU RAPIDO
echo               Reconhecimento Facial e Controle de Acesso
echo ============================================================================
echo.
echo   Escolha como deseja iniciar o programa (tudo opcional):
echo.
echo   [1] Executar versao 1-Clique (.EXE)
echo       (Nao precisa ter Python instalado nem baixar bibliotecas)
echo.
echo   [2] Rodar pelo Codigo-Fonte Python (v3.0\facesafety.py)
echo       (Verifica/instala o OpenCV automaticamente e permite usar a funcao KEY)
echo.
echo   [3] Modo Ambiente Virtual (Cria venv limpo + instala dependencias + abre)
echo       (Recomendado caso seu Python de erro de permissao no Windows)
echo.
echo   [4] Editar a funcao KEY no codigo-fonte (abre v3.0\facesafety.py)
echo.
echo   [0] Sair
echo.
echo ============================================================================
set /p OPCAO="Digite o numero da opcao desejada [Padrao=1]: "

if "%OPCAO%"=="" set OPCAO=1
if "%OPCAO%"=="1" goto RODAR_EXE
if "%OPCAO%"=="2" goto RODAR_PY
if "%OPCAO%"=="3" goto RODAR_VENV
if "%OPCAO%"=="4" goto EDITAR_KEY
if "%OPCAO%"=="0" exit /b 0

echo.
echo [!] Opcao invalida. Tente novamente.
timeout /t 2 >nul
goto MENU

:: ----------------------------------------------------------------------------
:: OPCAO 1: EXECUTAR .EXE DIRETO
:: ----------------------------------------------------------------------------
:RODAR_EXE
echo.
if exist "v3.0\FaceSafety-v3.0.exe" (
    echo [OK] Iniciando FaceSafety-v3.0.exe...
    start "" "v3.0\FaceSafety-v3.0.exe"
    exit /b 0
) else if exist "FaceSafety-v3.0.exe" (
    echo [OK] Iniciando FaceSafety-v3.0.exe...
    start "" "FaceSafety-v3.0.exe"
    exit /b 0
) else (
    echo [AVISO] O arquivo FaceSafety-v3.0.exe nao foi encontrado nesta pasta.
    echo Iniciando automaticamente pelo modo Python [Opcao 2]...
    timeout /t 2 >nul
    goto RODAR_PY
)

:: ----------------------------------------------------------------------------
:: OPCAO 2: VERIFICAR DEPENDENCIAS E RODAR O .PY DIRETO
:: ----------------------------------------------------------------------------
:RODAR_PY
echo.
echo [1/3] Verificando instalacao do Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado no sistema!
    echo Instale o Python 3.9+ em https://www.python.org/downloads/
    echo (Lembre-se de marcar a caixinha "Add Python to PATH" no instalador)
    echo Ou utilize a Opcao [1] para abrir o .EXE sem precisar do Python.
    echo.
    pause
    goto MENU
)

echo [2/3] Verificando biblioteca OpenCV (opencv-python)...
python -c "import cv2, numpy" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Instalando opencv-python e numpy (sem cache para evitar erros)...
    python -m pip install --no-cache-dir -r "v3.0\requirements.txt"
    if errorlevel 1 (
        echo.
        echo [AVISO] Falha na instalacao global. Tentando via Ambiente Virtual [Opcao 3]...
        goto RODAR_VENV
    )
) else (
    echo [OK] Dependencias ja estao instaladas!
)

echo [3/3] Abrindo Face Safety 3.0 (v3.0\facesafety.py)...
python "v3.0\facesafety.py"
if errorlevel 1 (
    echo.
    echo [!] Ocorreu um erro ao executar o script.
    pause
)
exit /b 0

:: ----------------------------------------------------------------------------
:: OPCAO 3: CRIAR AMBIENTE VIRTUAL (VENV) LIMPO E RODAR
:: ----------------------------------------------------------------------------
:RODAR_VENV
echo.
echo [1/4] Verificando instalacao do Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado no sistema!
    pause
    goto MENU
)

if not exist "v3.0\venv\Scripts\python.exe" (
    echo [2/4] Criando ambiente virtual isolado em v3.0\venv...
    python -m venv "v3.0\venv"
)

echo [3/4] Garantindo que o OpenCV esteja instalado no venv...
"v3.0\venv\Scripts\python.exe" -c "import cv2, numpy" >nul 2>&1
if errorlevel 1 (
    "v3.0\venv\Scripts\python.exe" -m pip install --no-cache-dir -r "v3.0\requirements.txt"
)

echo [4/4] Iniciando Face Safety 3.0 dentro do ambiente virtual...
"v3.0\venv\Scripts\python.exe" "v3.0\facesafety.py"
if errorlevel 1 (
    echo.
    echo [!] Ocorreu um erro ao executar o script.
    pause
)
exit /b 0

:: ----------------------------------------------------------------------------
:: OPCAO 4: ABRIR ARQUIVO PARA EDITAR FUNCAO KEY()
:: ----------------------------------------------------------------------------
:EDITAR_KEY
echo.
echo Abrindo v3.0\facesafety.py no Bloco de Notas...
echo Procure por "def key(" no final do arquivo para personalizar!
start notepad "v3.0\facesafety.py"
timeout /t 2 >nul
goto MENU
