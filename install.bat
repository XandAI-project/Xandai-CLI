@echo off
REM Script de instalação do XandAI para Windows

echo ╔═══════════════════════════════════════╗
echo ║     Instalando XandAI CLI...          ║
echo ╚═══════════════════════════════════════╝
echo.

REM Verifica se Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Erro: Python não encontrado. Instale Python 3.10 ou superior.
    pause
    exit /b 1
)

echo ✓ Python detectado
echo.

REM Pergunta sobre ambiente virtual
set /p create_venv="Deseja criar um ambiente virtual? (s/n): "
if /i "%create_venv%"=="s" (
    echo Criando ambiente virtual...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo ✓ Ambiente virtual criado e ativado
    echo.
)

REM Instala o pacote
echo Instalando XandAI...
pip install -e .

if %errorlevel% equ 0 (
    echo.
    echo ✅ XandAI instalado com sucesso!
    echo.
    echo Para começar a usar, execute:
    echo   xandai
    echo.
    echo Para ver a ajuda:
    echo   xandai --help
    echo.
    
    REM Verifica se OLLAMA está instalado
    where ollama >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✓ OLLAMA detectado
    ) else (
        echo ⚠️  OLLAMA não detectado. Instale em: https://ollama.ai
    )
) else (
    echo.
    echo ❌ Erro durante a instalação
    pause
    exit /b 1
)

pause
