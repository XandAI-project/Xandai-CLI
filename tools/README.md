# XandAI CLI Tools

Este diretório contém ferramentas customizadas que podem ser chamadas pelo agente LLM.

## Como Criar uma Ferramenta

Cada ferramenta é um arquivo Python que deve implementar:

1. **Classe da Ferramenta** com métodos:
   - `get_name()`: Nome da ferramenta
   - `get_description()`: Descrição do que a ferramenta faz
   - `get_parameters()`: Parâmetros que a ferramenta aceita
   - `execute(**kwargs)`: Lógica de execução

### Exemplo: weather_tool.py

```python
class WeatherTool:
    @staticmethod
    def get_name():
        return "weather_tool"

    @staticmethod
    def get_description():
        return "Get weather information for a location"

    @staticmethod
    def get_parameters():
        return {
            "location": "string (required) - City or location name",
            "date": "string (optional) - Date (default: now)"
        }

    def execute(self, location, date="now"):
        # Implementar lógica aqui
        return {"temperature": 25, "condition": "sunny"}
```

## Como Funciona

1. O usuário digita em linguagem natural: "what is the weather in los angeles now?"
2. O sistema detecta que existe uma ferramenta `weather_tool`
3. Converte para chamada estruturada com parâmetros
4. Executa a ferramenta e retorna o resultado
5. O LLM interpreta e formata a resposta final

## Ferramentas Disponíveis

Atualmente não há ferramentas instaladas. Adicione seus próprios arquivos `.py` neste diretório!
