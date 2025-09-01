# Instruções Aprimoradas de Tags Especiais

## Melhorias Implementadas

As instruções básicas de tags agora incluem **exemplos claros de uso correto e incorreto** para garantir que os modelos LLM entendam exatamente como usar as tags especiais.

## Formato das Instruções Aprimoradas

### 1. **Tags para Comandos Shell (`<actions>`)**

**✅ CORRETO:**
```xml
<actions>mkdir my-project</actions>
<actions>pip install flask</actions>
```

**❌ INCORRETO:**
```bash
mkdir my-project
```
Ou simplesmente descrever: "Create a folder called my-project"

### 2. **Tags para Criação/Edição de Arquivos (`<code>`)**

**✅ CORRETO:**
```xml
<code filename="app.py">
from flask import Flask
app = Flask(__name__)
</code>
```

**❌ INCORRETO:**
```python
from flask import Flask
app = Flask(__name__)
```
Ou simplesmente descrever: "Create an app.py file with Flask imports"

### 3. **Tags para Leitura de Arquivos (`<read>`)**

**✅ CORRETO:**
```xml
<read>cat app.py</read>
<read>ls -la</read>
```

**❌ INCORRETO:**
```bash
cat app.py
```
Ou simplesmente descrever: "Check the contents of app.py"

## Regras Críticas Incluídas

As instruções agora enfatizam:

- ✅ **SEMPRE** use `<actions>` para comandos (mkdir, pip, npm, git, etc.)
- ✅ **SEMPRE** use `<code filename="...">` para criação/edição de arquivos  
- ✅ **SEMPRE** use `<read>` para examinar arquivos
- ❌ **NUNCA** use blocos ``` para arquivos que devem ser criados
- ❌ **NUNCA** apenas descreva ações - use as tags!

## Benefícios da Melhoria

### 1. **Clareza Visual**
- Uso de ✅ e ❌ para destacar exemplos corretos e incorretos
- Exemplos lado a lado para comparação direta

### 2. **Exemplos Práticos**
- Mostra exatamente como formatar cada tipo de tag
- Inclui casos reais de uso (Flask app, comandos comuns)

### 3. **Prevenção de Erros**
- Explica explicitamente o que NÃO fazer
- Evita confusão entre blocos ``` e tags especiais

### 4. **Aplicação Automática**
- Estas instruções são adicionadas automaticamente quando o sistema detecta que o usuário precisa de ações automatizadas
- Funciona mesmo com enhancement desabilitado

## Impacto na Experiência do Usuário

Com essas instruções aprimoradas, os modelos LLM agora têm:

- **Orientação clara** sobre formato correto das tags
- **Exemplos visuais** de uso correto vs incorreto  
- **Regras explícitas** para evitar erros comuns
- **Contexto prático** com exemplos reais

Isso garante que as tags `<actions>`, `<code>`, e `<read>` sejam usadas corretamente, resultando em **execução automática consistente** de comandos e criação de arquivos.

## Resultado Final

O CLI agora fornece **instruções educativas e visuais** que tornam o uso das tags especiais mais intuitivo e confiável para qualquer modelo LLM, garantindo que as ações sejam executadas automaticamente conforme esperado pelo usuário.
