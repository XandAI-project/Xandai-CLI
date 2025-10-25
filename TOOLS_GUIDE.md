# XandAI CLI - Sistema de Ferramentas Customizadas

## Visão Geral

O XandAI CLI agora possui um sistema de ferramentas customizadas que permite estender as capacidades do agente através de plugins Python. As ferramentas são automaticamente detectadas e podem ser invocadas através de linguagem natural.

## Como Funciona

1. **Detecção Automática**: Ferramentas são carregadas automaticamente do diretório `/tools`
2. **Conversão Inteligente**: O LLM converte linguagem natural em chamadas de ferramentas
3. **Execução**: A ferramenta é executada com os parâmetros extraídos
4. **Interpretação**: O resultado é enviado de volta ao LLM para interpretação e formatação

## Criando uma Ferramenta

### Estrutura Básica

Crie um arquivo Python em `/tools` com a seguinte estrutura:

```python
class MinhaFerramenta:
    @staticmethod
    def get_name():
        """Nome único da ferramenta"""
        return "minha_ferramenta"

    @staticmethod
    def get_description():
        """Descrição do que a ferramenta faz"""
        return "Descrição clara da funcionalidade"

    @staticmethod
    def get_parameters():
        """Parâmetros aceitos pela ferramenta"""
        return {
            "parametro1": "tipo (obrigatório/opcional) - Descrição",
            "parametro2": "tipo (opcional) - Descrição com valor padrão"
        }

    def execute(self, parametro1, parametro2="valor_padrao"):
        """
        Lógica de execução da ferramenta

        Args:
            parametro1: Descrição do parâmetro
            parametro2: Descrição do parâmetro opcional

        Returns:
            Dicionário ou estrutura de dados com o resultado
        """
        # Sua lógica aqui
        resultado = {
            "status": "success",
            "data": "seus dados"
        }
        return resultado
```

### Exemplo Completo: Weather Tool

```python
# tools/weather_tool.py

from datetime import datetime
import requests

class WeatherTool:
    @staticmethod
    def get_name():
        return "weather_tool"

    @staticmethod
    def get_description():
        return "Get current weather information for any location"

    @staticmethod
    def get_parameters():
        return {
            "location": "string (required) - City or location name",
            "date": "string (optional) - Date for weather (default: now)"
        }

    def execute(self, location: str, date: str = "now"):
        # Aqui você integraria com uma API real
        # Este é apenas um exemplo com dados mockados

        result = {
            "location": location,
            "date": date if date != "now" else datetime.now().strftime("%Y-%m-%d"),
            "weather": {
                "temperature": 25,
                "condition": "sunny",
                "humidity": 45
            }
        }
        return result
```

## Usando as Ferramentas

### No Chat Interativo

Basta digitar em linguagem natural:

```
xandai> what is the weather in Los Angeles now?
🔧 Calling tool: weather_tool
📝 Arguments: {"location": "los angeles", "date": "now"}
✓ Tool executed successfully

╭─ 🤖 XandAI ─╮
│ The current weather in Los Angeles is sunny with a temperature of 25°C... │
╰─────────────╯
```

### Comandos Especiais

```bash
# Listar ferramentas disponíveis
xandai> /tools

# Ver ajuda completa
xandai> /help
```

## Exemplos de Ferramentas

### 1. Ferramenta de Calculadora

```python
# tools/calculator_tool.py

import math

class CalculatorTool:
    @staticmethod
    def get_name():
        return "calculator"

    @staticmethod
    def get_description():
        return "Perform mathematical calculations"

    @staticmethod
    def get_parameters():
        return {
            "expression": "string (required) - Mathematical expression to evaluate",
            "precision": "int (optional) - Decimal precision (default: 2)"
        }

    def execute(self, expression: str, precision: int = 2):
        try:
            # ATENÇÃO: Em produção, use uma biblioteca segura como numexpr
            # eval() pode ser perigoso com entrada não confiável
            result = eval(expression, {"__builtins__": None}, {"math": math})
            return {
                "expression": expression,
                "result": round(result, precision),
                "status": "success"
            }
        except Exception as e:
            return {
                "expression": expression,
                "error": str(e),
                "status": "error"
            }
```

### 2. Ferramenta de Busca em Arquivos

```python
# tools/file_search_tool.py

import os
from pathlib import Path

class FileSearchTool:
    @staticmethod
    def get_name():
        return "file_search"

    @staticmethod
    def get_description():
        return "Search for files in the project directory"

    @staticmethod
    def get_parameters():
        return {
            "pattern": "string (required) - File name pattern to search",
            "directory": "string (optional) - Directory to search (default: current)",
            "recursive": "bool (optional) - Search recursively (default: True)"
        }

    def execute(self, pattern: str, directory: str = ".", recursive: bool = True):
        search_path = Path(directory)

        if recursive:
            files = list(search_path.rglob(pattern))
        else:
            files = list(search_path.glob(pattern))

        return {
            "pattern": pattern,
            "directory": str(directory),
            "found_files": [str(f) for f in files],
            "count": len(files)
        }
```

### 3. Ferramenta de Dados de API

```python
# tools/api_tool.py

import requests

class APITool:
    @staticmethod
    def get_name():
        return "api_fetch"

    @staticmethod
    def get_description():
        return "Fetch data from REST APIs"

    @staticmethod
    def get_parameters():
        return {
            "url": "string (required) - API endpoint URL",
            "method": "string (optional) - HTTP method (default: GET)",
            "headers": "dict (optional) - HTTP headers"
        }

    def execute(self, url: str, method: str = "GET", headers: dict = None):
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers or {},
                timeout=10
            )

            return {
                "url": url,
                "status_code": response.status_code,
                "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                "success": response.ok
            }
        except Exception as e:
            return {
                "url": url,
                "error": str(e),
                "success": False
            }
```

## Boas Práticas

### 1. Segurança
- Nunca execute código arbitrário sem validação
- Use bibliotecas seguras para operações sensíveis
- Valide todos os inputs antes de processar

### 2. Tratamento de Erros
- Sempre capture exceções
- Retorne mensagens de erro claras
- Inclua informações úteis para debug

### 3. Documentação
- Use docstrings claras
- Descreva todos os parâmetros
- Inclua exemplos de uso

### 4. Performance
- Adicione timeouts para operações de rede
- Cache resultados quando apropriado
- Evite operações bloqueantes demoradas

## Fluxo de Execução

```
Usuário digita em linguagem natural
           ↓
Sistema verifica se existe ferramenta correspondente
           ↓
LLM converte entrada em chamada estruturada
           ↓
Ferramenta é executada com parâmetros
           ↓
Resultado é enviado ao LLM para interpretação
           ↓
Resposta formatada é exibida ao usuário
```

## Testando suas Ferramentas

Use o script de teste fornecido:

```bash
python test_tools_system.py
```

Ou crie testes específicos para sua ferramenta:

```python
from xandai.utils.tool_manager import ToolManager

def test_minha_ferramenta():
    tool_manager = ToolManager(tools_dir="tools")
    result = tool_manager.execute_tool("minha_ferramenta", {
        "parametro": "valor"
    })
    print(result)
```

## Troubleshooting

### Ferramenta não está sendo carregada
- Verifique se o arquivo está em `/tools`
- Certifique-se que a classe implementa todos os métodos necessários
- Verifique se não há erros de sintaxe no arquivo

### Ferramenta não está sendo invocada
- Use `/tools` para ver se a ferramenta foi carregada
- Verifique a descrição da ferramenta - ela deve ser clara sobre o que faz
- O LLM precisa entender quando usar a ferramenta baseado na descrição

### Erro na execução
- Adicione tratamento de exceções no método `execute()`
- Use logs para debug (`print()` ou logging)
- Teste a ferramenta isoladamente primeiro

## Contribuindo

Para contribuir com novas ferramentas:

1. Crie sua ferramenta seguindo a estrutura acima
2. Adicione testes
3. Documente o uso
4. Compartilhe com a comunidade!

## Exemplos de Uso Reais

```
# Buscar arquivos
xandai> find all Python files in the project

# Fazer cálculos
xandai> calculate the square root of 144

# Buscar informações
xandai> what's the weather like in Tokyo?

# Consultar APIs
xandai> fetch data from https://api.example.com/users

# Buscar em código
xandai> search for files containing 'TODO' in src/
```

## Recursos Adicionais

- Diretório de ferramentas: `/tools`
- Documentação do sistema: `xandai/utils/tool_manager.py`
- Script de teste: `test_tools_system.py`
- Exemplo completo: `tools/weather_tool.py`

---

**Nota**: O sistema de ferramentas é extensível e você pode criar quantas ferramentas precisar para seu workflow específico!
