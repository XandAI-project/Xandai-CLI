#!/bin/bash
# Script de instalação rápida do XandAI

echo "╔═══════════════════════════════════════╗"
echo "║     Instalando XandAI CLI...          ║"
echo "╚═══════════════════════════════════════╝"
echo

# Verifica se Python 3.10+ está instalado
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then 
    echo "❌ Erro: Python $required_version ou superior é necessário (encontrado: $python_version)"
    exit 1
fi

echo "✓ Python $python_version detectado"

# Cria ambiente virtual (opcional)
read -p "Deseja criar um ambiente virtual? (s/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo "Criando ambiente virtual..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✓ Ambiente virtual criado e ativado"
fi

# Instala o pacote
echo "Instalando XandAI..."
pip install -e .

if [ $? -eq 0 ]; then
    echo
    echo "✅ XandAI instalado com sucesso!"
    echo
    echo "Para começar a usar, execute:"
    echo "  $ xandai"
    echo
    echo "Para ver a ajuda:"
    echo "  $ xandai --help"
    echo
    
    # Verifica se OLLAMA está instalado
    if command -v ollama &> /dev/null; then
        echo "✓ OLLAMA detectado"
    else
        echo "⚠️  OLLAMA não detectado. Instale em: https://ollama.ai"
    fi
else
    echo
    echo "❌ Erro durante a instalação"
    exit 1
fi
