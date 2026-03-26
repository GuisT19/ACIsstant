@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo   Antigravity - Instalador para Windows 11
echo ============================================================
echo.

:: ---------------------------------------------------------------
:: Obter o caracter CR (usado para overwrite da linha do spinner)
:: ---------------------------------------------------------------
for /f %%A in ('copy /Z "%COMSPEC%" nul') do set "CR=%%A"

:: Caracteres do spinner (evitar | para nao ser interpretado como pipe)
set "SP0=/"
set "SP1=-"
set "SP2=\\"
set "SP3=*"

:: ---------------------------------------------------------------
:: Step 1: Verificar Python
:: ---------------------------------------------------------------
echo [1/5] A verificar instalacao do Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERRO] Python nao encontrado no PATH.
    echo Por favor instala o Python 3.10 ou superior em:
    echo   https://www.python.org/downloads/
    echo.
    echo IMPORTANTE: durante a instalacao do Python, marca a opcao
    echo             "Add Python to PATH"
    echo.
    pause
    exit /b 1
)
python --version
echo [OK] Python encontrado.
echo.

:: ---------------------------------------------------------------
:: Step 2: Criar ambiente virtual
:: ---------------------------------------------------------------
echo [2/5] A criar ambiente virtual (venv)...
if exist venv\ (
    echo [OK] Ambiente venv ja existe. A saltar criacao.
) else (
    python -m venv venv
    if errorlevel 1 (
        echo [ERRO] Falha ao criar o ambiente virtual.
        pause
        exit /b 1
    )
    echo [OK] Ambiente virtual criado com sucesso.
)
echo.

:: Ativar o venv — tudo o que se segue instala dentro do venv
call venv\Scripts\activate.bat
venv\Scripts\python -m pip install --upgrade pip --quiet
echo [OK] Ambiente virtual ativado e pip atualizado.
echo.

:: ---------------------------------------------------------------
:: Step 3: Instalar llama-cpp-python (com spinner)
:: ---------------------------------------------------------------
echo [3/5] A instalar llama-cpp-python...
echo       (Sem compilador C++ disponivel, usa wheels pre-compiladas.)
echo       (Pode demorar varios minutos. Por favor aguarda.)
echo.

:: Limpar ficheiros de sessoes anteriores
if exist "%TEMP%\_aci_done.txt" del "%TEMP%\_aci_done.txt" >nul 2>&1
if exist "%TEMP%\_aci_log.txt"  del "%TEMP%\_aci_log.txt"  >nul 2>&1
if exist "%TEMP%\_aci_run.bat"  del "%TEMP%\_aci_run.bat"  >nul 2>&1

:: Escrever script auxiliar de instalacao (tenta 2 fontes de wheels)
(
    echo @echo off
    echo cd /d "%CD%"
    echo venv\Scripts\pip install llama-cpp-python --only-binary :all: --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu --quiet ^>^>"%TEMP%\_aci_log.txt" 2^>^&1
    echo if not errorlevel 1 ^(echo OK^>"%TEMP%\_aci_done.txt" ^& exit /b 0^)
    echo venv\Scripts\pip install llama-cpp-python --only-binary :all: --quiet ^>^>"%TEMP%\_aci_log.txt" 2^>^&1
    echo if not errorlevel 1 ^(echo OK^>"%TEMP%\_aci_done.txt" ^& exit /b 0^)
    echo echo FAIL^>"%TEMP%\_aci_done.txt"
) > "%TEMP%\_aci_run.bat"

:: Iniciar instalacao em background
start /b "" cmd /c "%TEMP%\_aci_run.bat"

:: Spinner enquanto instala
set ELAPSED=0
set SIDX=0

:LLAMA_SPIN
if exist "%TEMP%\_aci_done.txt" goto LLAMA_DONE
set /a SIDX=SIDX %% 4
if !SIDX!==0 (set "SYM=!SP0!") else if !SIDX!==1 (set "SYM=!SP1!") else if !SIDX!==2 (set "SYM=!SP2!") else (set "SYM=!SP3!")
set /a SIDX+=1
set /a T_MIN=ELAPSED/60
set /a T_SEC=ELAPSED %% 60
if !T_SEC! LSS 10 (set "T_SEC=0!T_SEC!")
<nul set /p "=    llama-cpp-python  !SYM!  [!T_MIN!m !T_SEC!s]            %CR%"
timeout /t 1 /nobreak >nul
set /a ELAPSED+=1
goto LLAMA_SPIN

:LLAMA_DONE
set /a T_MIN=ELAPSED/60
set /a T_SEC=ELAPSED %% 60
if !T_SEC! LSS 10 (set "T_SEC=0!T_SEC!")
<nul set /p "=    llama-cpp-python  OK  [!T_MIN!m !T_SEC!s]               "
echo.

:: Verificar resultado
findstr /c:"OK" "%TEMP%\_aci_done.txt" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERRO] Nao foi possivel instalar llama-cpp-python via wheel pre-compilada.
    echo.
    echo Para resolver, instala o Visual C++ Build Tools:
    echo   https://visualstudio.microsoft.com/visual-cpp-build-tools/
    echo.
    echo Durante a instalacao, seleciona:
    echo   "Desktop development with C++"
    echo.
    echo Depois volta a correr este script.
    del "%TEMP%\_aci_done.txt" >nul 2>&1
    del "%TEMP%\_aci_log.txt"  >nul 2>&1
    del "%TEMP%\_aci_run.bat"  >nul 2>&1
    pause
    exit /b 1
)
echo [OK] llama-cpp-python instalado no venv.
del "%TEMP%\_aci_done.txt" >nul 2>&1
del "%TEMP%\_aci_log.txt"  >nul 2>&1
del "%TEMP%\_aci_run.bat"  >nul 2>&1
echo.

:: ---------------------------------------------------------------
:: Step 4: Instalar restantes dependencias (com spinner)
:: ---------------------------------------------------------------
echo [4/5] A instalar restantes dependencias...
echo.

:: Limpar ficheiros de sessoes anteriores
if exist "%TEMP%\_aci2_done.txt" del "%TEMP%\_aci2_done.txt" >nul 2>&1
if exist "%TEMP%\_aci2_log.txt"  del "%TEMP%\_aci2_log.txt"  >nul 2>&1
if exist "%TEMP%\_aci2_run.bat"  del "%TEMP%\_aci2_run.bat"  >nul 2>&1

:: Escrever script auxiliar de instalacao
(
    echo @echo off
    echo cd /d "%CD%"
    echo venv\Scripts\pip install fastapi uvicorn pydantic langchain langchain-community langchain-text-splitters langchain-huggingface faiss-cpu sentence-transformers huggingface_hub python-multipart psutil pypdf --quiet ^>^>"%TEMP%\_aci2_log.txt" 2^>^&1
    echo if not errorlevel 1 ^(echo OK^>"%TEMP%\_aci2_done.txt"^) else ^(echo FAIL^>"%TEMP%\_aci2_done.txt"^)
) > "%TEMP%\_aci2_run.bat"

:: Iniciar instalacao em background
start /b "" cmd /c "%TEMP%\_aci2_run.bat"

:: Spinner enquanto instala
set ELAPSED=0
set SIDX=0

:DEPS_SPIN
if exist "%TEMP%\_aci2_done.txt" goto DEPS_DONE
set /a SIDX=SIDX %% 4
if !SIDX!==0 (set "SYM=!SP0!") else if !SIDX!==1 (set "SYM=!SP1!") else if !SIDX!==2 (set "SYM=!SP2!") else (set "SYM=!SP3!")
set /a SIDX+=1
set /a T_MIN=ELAPSED/60
set /a T_SEC=ELAPSED %% 60
if !T_SEC! LSS 10 (set "T_SEC=0!T_SEC!")
<nul set /p "=    Dependencias Python  !SYM!  [!T_MIN!m !T_SEC!s]         %CR%"
timeout /t 1 /nobreak >nul
set /a ELAPSED+=1
goto DEPS_SPIN

:DEPS_DONE
set /a T_MIN=ELAPSED/60
set /a T_SEC=ELAPSED %% 60
if !T_SEC! LSS 10 (set "T_SEC=0!T_SEC!")
<nul set /p "=    Dependencias Python  OK  [!T_MIN!m !T_SEC!s]            "
echo.

:: Verificar resultado
findstr /c:"OK" "%TEMP%\_aci2_done.txt" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao instalar algumas dependencias.
    echo Verifica a tua ligacao a internet e volta a tentar.
    del "%TEMP%\_aci2_done.txt" >nul 2>&1
    del "%TEMP%\_aci2_log.txt"  >nul 2>&1
    del "%TEMP%\_aci2_run.bat"  >nul 2>&1
    pause
    exit /b 1
)
echo [OK] Todas as dependencias instaladas no venv.
del "%TEMP%\_aci2_done.txt" >nul 2>&1
del "%TEMP%\_aci2_log.txt"  >nul 2>&1
del "%TEMP%\_aci2_run.bat"  >nul 2>&1
echo.

:: ---------------------------------------------------------------
:: Step 5: Criar diretorios necessarios
:: ---------------------------------------------------------------
echo [5/5] A criar estrutura de diretorios...
if not exist models\       mkdir models
if not exist data\uploads\ mkdir data\uploads
if not exist data\vectordb\ mkdir data\vectordb
echo [OK] Diretorios criados.
echo.

:: ---------------------------------------------------------------
:: Conclusao
:: ---------------------------------------------------------------
echo ============================================================
echo   Instalacao concluida com sucesso!
echo ============================================================
echo.
echo Proximos passos:
echo   1. Descarrega o modelo IA:
echo        venv\Scripts\python download_model.py
echo.
echo   2. Inicia o assistente:
echo        run.bat
echo.
echo   3. Abre o browser em:
echo        http://localhost:8000
echo.
pause
