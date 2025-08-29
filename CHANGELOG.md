# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.5.3] - 2024-01-XX

### 🔍 ENHANCEMENT - Intelligent File and Directory Search

#### 📁 Directory Search When File Not Found
- **Intelligent behavior**: If file is not found, searches for similar directories
- **Navigation suggestion**: System suggests navigating to found directories
- **Recursive search**: After navigating, user can search for file again

#### 🎯 Enhanced Search Features
1. **Primary search**: Tries to find the file normally
2. **Secondary search**: If it fails, searches for directories with similar names
3. **Pattern search**: Finds variations (case-insensitive, without extension)
4. **Interactive interface**: Menu to choose directory or similar file

#### 💡 Exemplo de Uso
```
/file search Documentation.md

❌ Arquivo não encontrado
📁 Diretórios encontrados:
  1. C:\Users\kevin\youtube-clone\youtube-clone
  2. C:\Users\kevin\youtube-clone\docs

Digite o número do diretório para navegar: 1

✓ Navegado para: C:\Users\kevin\youtube-clone\youtube-clone
💡 Tente buscar o arquivo novamente com /file search
```

#### 🎨 Melhorias Adicionais
- **Arquivos similares**: Lista até 5 arquivos com nomes parecidos
- **Navegação facilitada**: Usa caminhos relativos para comando cd
- **Múltiplas opções**: Interface permite escolher entre vários resultados
- **Feedback claro**: Mensagens indicam próximos passos

## [0.5.2] - 2024-01-XX

### 🎯 NOVA FUNCIONALIDADE - Tarefas Essenciais vs Opcionais

#### 📊 Categorização de Tarefas
- **Tarefas marcadas**: Cada tarefa agora é categorizada como [ESSENCIAL] ou [OPCIONAL]
- **Detecção automática**: Sistema detecta automaticamente a prioridade baseado em palavras-chave
- **Marcadores explícitos**: LLM marca cada tarefa com [ESSENCIAL] ou [OPCIONAL]

#### 🎮 Menu de Escolha Interativo
Após o plano ser criado, o usuário pode escolher:
1. **Executar apenas ESSENCIAIS**: Foca no mínimo necessário para funcionar
2. **Executar TODAS**: Inclui melhorias e recursos extras
3. **Cancelar**: Aborta a execução

#### 📋 Critérios de Classificação

**Tarefas ESSENCIAIS incluem:**
- Documentation.md (sempre primeira tarefa)
- Estrutura básica do projeto
- Configuração de ambiente
- Funcionalidades principais
- Modelos de dados
- Autenticação/segurança básica
- APIs principais

**Tarefas OPCIONAIS incluem:**
- Testes unitários
- Otimizações de performance
- Sistema de cache
- Logging avançado
- Documentação adicional
- Recursos extras/avançados

#### 🎨 Exemplo de Execução
```
/task criar blog com Django

✅ Plano de Execução Criado!

┌─── Progresso das Tarefas ───┐
│ ⏳ [E] Tarefa 1: Criar arquivo Documentation.md...       │
│ ⏳ [E] Tarefa 2: Configurar ambiente Django              │
│ ⏳ [E] Tarefa 3: Criar modelos Post e User              │
│ ⏳ [E] Tarefa 4: Implementar views e templates          │
│ ⏳ [O] Tarefa 5: Adicionar testes unitários             │
│ ⏳ [O] Tarefa 6: Implementar sistema de cache           │
│ ⏳ [O] Tarefa 7: Adicionar analytics                    │
└────────────────────────────────────────────────────────┘

📊 Resumo:
   Essenciais: 4 tarefas
   Opcionais: 3 tarefas

Escolha uma opção:
  1. Executar apenas tarefas ESSENCIAIS
  2. Executar TODAS as tarefas (essenciais + opcionais)  
  3. Cancelar

Sua escolha (1/2/3): 1

✓ Executando 4 tarefas essenciais
```

## [0.5.1] - 2024-01-XX

### 🎯 MELHORIAS - Contexto Persistente e Documentação Automática

#### 1️⃣ Contexto de Linguagem/Framework Mantido Entre Tarefas
- **Detecção automática**: Sistema detecta linguagem e framework na requisição inicial
- **Contexto global**: Informação é mantida durante toda a execução das tarefas
- **Todas as tarefas**: Cada tarefa recebe o contexto de linguagem/framework
- **Exemplo**:
  ```
  User: /task criar API REST em Python com Flask
  → Detecta: Language: python, Framework: Flask
  → TODAS as tarefas subsequentes mantêm esse contexto
  ```

#### 2️⃣ Primeira Tarefa Sempre é Documentation.md
- **Padrão obrigatório**: Primeira tarefa sempre cria Documentation.md
- **Escopo completo**: Inclui objetivos, funcionalidades, estrutura e tecnologias
- **Contexto preservado**: Recebe a requisição original completa
- **Conteúdo do Documentation.md**:
  - Visão geral e objetivos do projeto
  - Lista completa de funcionalidades
  - Arquitetura técnica e estrutura
  - Tecnologias, linguagens e frameworks usados
  - Roadmap de desenvolvimento
  
#### 🎨 Exemplo de Execução
```
/task criar um e-commerce com React e Node.js

🔍 Linguagem detectada: javascript
🔍 Framework detectado: React

Tarefas geradas:
1. Criar arquivo Documentation.md com escopo completo do projeto
2. Configurar ambiente backend com Node.js
3. Criar estrutura do frontend com React
...

[Language: javascript]
[Framework: React]
[Task 1 of 8]
[Original Project Request: criar um e-commerce com React e Node.js]
```

## [0.5.0] - 2024-01-XX

### 🚀 MAJOR UPDATE - AI Melhorado e Git Automático

#### 1️⃣ AI Sempre Gera Arquivos Completos
- **Instruções melhoradas**: AI agora SEMPRE inclui o arquivo completo nas tags `<code>`
- **Sem outputs parciais**: Proibido usar "..." ou "rest of code remains the same"
- **Regras rígidas**: Mesmo mudando uma linha, AI deve outputar o arquivo inteiro
- **Benefício**: Evita perda de código e garante integridade dos arquivos

#### 2️⃣ Arquivos Existentes São Lidos Automaticamente
- **Contexto completo**: Quando um arquivo é mencionado, seu conteúdo é incluído no prompt
- **Edição inteligente**: AI recebe o arquivo completo antes de editar
- **Exemplo**:
  ```
  [EXISTING FILE CONTENT - app.py]:
  ```
  # Conteúdo completo do arquivo
  ```
  [END OF app.py]
  ⚠️ IMPORTANT: When editing this file, include the COMPLETE updated content!
  ```

#### 3️⃣ Git Commits Automáticos
- **Git init automático**: Se não existe .git, cria repositório automaticamente
- **Commits após cada operação**:
  - Arquivo criado: `XandAI: created filename.py`
  - Arquivo editado: `XandAI: edited filename.py`
  - Arquivo deletado: `XandAI: deleted filename.py`
- **Configuração automática**: Define user.name e user.email se necessário
- **Mensagens no console**:
  ```
  ✓ Repositório Git inicializado
  ✓ Git commit: XandAI: created app.py
  ```

#### 🎯 Benefícios Combinados
1. **Histórico completo**: Cada mudança é versionada automaticamente
2. **Sem perda de código**: AI sempre trabalha com arquivos completos
3. **Rastreabilidade**: Fácil ver o que foi mudado e quando
4. **Backup automático**: Git protege contra perda acidental

## [0.4.11] - 2024-01-XX

### 🔍 NOVA FUNCIONALIDADE - Busca Avançada de Arquivos

#### 🎯 Busca em Diretórios Pai e Subdiretórios
- **Novo comando**: `/file search <arquivo>` - Busca em diretórios pai e todos os subdiretórios
- **Melhoria**: `/file list` agora suporta flag `-r` para busca recursiva
- **Contexto expandido**: AI agora vê arquivos do diretório pai no contexto

#### ✅ Novos recursos:
1. **Busca inteligente de arquivos**:
   - Procura primeiro no diretório atual e subdiretórios
   - Se não encontrar, busca em até 3 níveis de diretórios pai
   - Mostra o progresso da busca em tempo real
   
2. **Listagem recursiva**:
   - `/file list -r` lista todos os arquivos recursivamente
   - `/file list . *.py -r` busca todos os .py recursivamente
   - Mostra caminhos relativos para melhor visualização

3. **Contexto melhorado**:
   - AI agora vê estrutura do diretório pai
   - Lista até 3 arquivos importantes do diretório pai
   - Mostra hierarquia completa do projeto

#### 📝 Exemplos de uso:
```bash
# Buscar arquivo em qualquer lugar
/file search config.json
🔍 Buscando 'config.json' em C:\projeto e subdiretórios...
🔍 Buscando em diretório pai: C:\
✓ Encontrado: C:\projeto_root\config.json

# Listar arquivos recursivamente
/file list . *.py -r

# Listar todos os arquivos HTML recursivamente
/file list templates *.html -r
```

#### 🎨 Melhorias no contexto do AI:
```
[Parent Directory: C:\Users\projeto]
Parent directory files:
  ../package.json
  ../README.md
  ../setup.py

[Current Directory: C:\Users\projeto\src]
  - main.py
  - utils.py
  - config.py
  - templates/ (3 files)
    - index.html
    - base.html
  - static/ (5 files)
```

## [0.4.10] - 2024-01-XX

### 🐛 CORREÇÕES - Comando /enhance_code

#### 🔧 Melhorias no Prompt Enhancement
- **Instruções mais diretas**: Prompt agora força o AI a usar tags `<code>` com exemplos claros
- **Detecção de falhas**: Sistema detecta quando AI não segue o formato correto
- **Mensagens de erro úteis**: Avisa o usuário quando o AI falha e sugere ações

#### 📝 Mudanças no Prompt:
- Adicionado formato OBRIGATÓRIO com passos numerados
- Incluído exemplo concreto de resposta correta
- Interpretação automática do pedido do usuário
- Avisos em CAPS LOCK sobre uso obrigatório de tags

#### 🛡️ Nova Validação:
```python
# Se em modo enhancement e AI não usou <code>:
⚠️  ERRO: O AI não seguiu o formato correto!
O AI deveria ter usado tags <code filename="..."> para editar os arquivos.
Tente novamente com uma descrição mais específica ou use um modelo diferente.
```

#### 💡 Problema Resolvido:
- AI estava apenas lendo arquivos sem editar
- Agora há verificação e feedback claro ao usuário
- Instruções mais explícitas forçam comportamento correto

## [0.4.9] - 2024-01-XX

### 🚀 NOVO COMANDO - /enhance_code

#### 🔧 Comando Dedicado para Melhorar Código Existente
- **Novo comando**: `/enhance_code <descrição>` para melhorar código existente
- **Funcionalidade**: Analisa e melhora APENAS arquivos existentes, nunca cria novos
- **Prompt Especializado**: Instruções específicas para enhancement de código

#### ✅ O que o comando faz:
1. **Adiciona mais detalhes**:
   - Tratamento de erros e exceções
   - Documentação e comentários
   - Type hints e tipagem adequada
   
2. **Corrige problemas**:
   - Bugs e erros de sintaxe
   - Problemas de linting
   - Vulnerabilidades de segurança
   
3. **Melhora qualidade**:
   - Nomes de variáveis mais descritivos
   - Estrutura e organização do código
   - Otimizações de performance

#### 📝 Exemplo de uso:
```bash
/enhance_code adicionar tratamento de erros e documentação

# O AI irá:
# 1. Analisar arquivos existentes
# 2. Identificar áreas de melhoria
# 3. EDITAR os arquivos (nunca criar novos)
# 4. Apresentar análise e mudanças feitas
```

#### ❌ Regras rígidas:
- NUNCA cria arquivos novos
- NUNCA remove funcionalidades existentes
- SEMPRE usa tags `<code filename="existing.py">` para edições
- Foca apenas em melhorias, não em mudanças de funcionalidade

## [0.4.8] - 2024-01-XX

### 🚀 NOVA FUNCIONALIDADE - Contexto de Estrutura de Arquivos
- **📁 Estrutura de Arquivos no Contexto**: AI agora recebe informação sobre arquivos existentes
  - Lista automática de arquivos e diretórios existentes
  - Previne criação de arquivos duplicados
  - Incentiva edição de arquivos existentes

- **🎯 Detecção Inteligente**: Sistema mostra ao AI:
  - Quantos arquivos existem e em quantos diretórios
  - Lista de arquivos principais (.py, .js, .html, etc.)
  - Estrutura de subdiretórios com seus arquivos
  - Mensagem clara: "[IMPORTANT: Edit existing files instead of creating duplicates!]"

- **📝 Regras de Manuseio de Arquivos Aprimoradas**:
  - Se app.py existe → EDITAR, não criar app2.py ou templates/app.py
  - Se templates/index.html existe → EDITAR, não criar templates/templates/index.html
  - Nunca colocar arquivos Python dentro de templates/
  - Evitar nomes genéricos como newfile.py, code.py

### 🎨 Exemplo de Contexto Enviado ao AI
```
[Working Directory: /path/to/project]

[Existing File Structure:]
Project has 2 files in 2 directories:
  - app.py
  - templates/
    - index.html

[IMPORTANT: Edit existing files instead of creating duplicates!]
```

## [0.4.7] - 2024-01-XX

### 🐛 CORREÇÃO CRÍTICA - Estruturas de Diretório e Duplicações
- **🚫 Filtro de Comandos**: Tags `<actions>` e `<read>` agora filtram comandos válidos
  - Ignora linhas de descrição em linguagem natural
  - Processa apenas comandos shell reais
  - Exemplo: "Create a folder" é ignorado, apenas "mkdir folder" é executado

- **📁 Prevenção de Estruturas Bizarras**: Instruções melhoradas para evitar:
  - Diretórios aninhados desnecessários (project/project/project)
  - Criação de pastas com nomes de descrição ("Create", "folder", "to", "hold")
  - Duplicação de arquivos em múltiplos locais

- **📝 Instruções Mais Claras**: Prompt enhancer agora mostra exemplos de uso:
  - ❌ ERRADO: `<actions>Create a folder to hold templates\nmkdir templates</actions>`
  - ✅ CERTO: `<actions>mkdir templates</actions>`

### 🎨 Melhorias nas Instruções
- **Regras de Estrutura de Diretório**: 
  - Criar estruturas simples e planas quando possível
  - Apenas diretórios necessários (ex: templates/ para Flask)
  - Evitar diretórios intermediários desnecessários

- **Debug Mode**: Mostra quando descrições são ignoradas nas tags

## [0.4.6] - 2024-01-XX

### 🐛 Corrigido (Modo Task)
- **🎯 Tags no Modo Task**: O comando `/task` agora processa corretamente tags especiais
  - Corrigido: tarefas individuais não estavam criando/editando arquivos
  - Adicionado: processamento de `<code>`, `<actions>`, `<read>` em `_execute_task`
  - Melhorado: mesmo fluxo de processamento do modo normal

- **📝 Instruções Mandatórias**: Task manager agora inclui instruções específicas por tipo
  - Tarefas de código: `[MANDATORY: Use <code filename="name.ext"> tags]`
  - Tarefas shell: `[MANDATORY: Use <actions> tags]`
  - Tarefas mistas: instruções para todas as tags

- **🔄 Detecção de Edição**: Detecta quando tarefa requer editar arquivo existente
  - Palavras-chave: "import", "adicione", "modifique", "edit"
  - Instrução: mostrar conteúdo COMPLETO do arquivo, não apenas linhas novas

### 🎨 Melhorias no Modo Task
- **Debug Visual**: Mostra quando modelo não usa tags em tarefas
- **Ordem de Processamento**: Tags especiais processadas antes de blocos ```
- **Feedback**: Avisa quando modelo deveria usar tags específicas

## [0.4.5] - 2024-01-XX

### 🚀 Melhorado (Nomeação Inteligente de Arquivos)
- **🎯 Nomeação Inteligente**: Sistema analisa contexto e código para gerar nomes apropriados
  - Detecta frameworks (Flask → `app.py`, FastAPI → `main.py`)
  - Extrai nomes do contexto (`crie fibonacci.py` → `fibonacci.py`)
  - Analisa código (classes, funções) para sugerir nomes
  - Prioriza nomes específicos sobre genéricos

- **📝 Edição vs Criação**: Edita arquivos existentes em vez de criar duplicatas
  - Se `app.py` existe, edita em vez de criar `app_timestamp.py`
  - Avisa quando arquivo será editado: `📝 app.py já existe - será editado`
  - Evita arquivos com timestamps desnecessários

- **🧹 Cleanup Automático**: Remove lógica de criação de arquivos genéricos
  - Nunca mais `code.py`, `code_20250822.py`
  - Nomes contextuais: `calculator.py`, `fibonacci.py`, `backup.py`
  - Fallbacks inteligentes: Python → `main.py`, JS → `index.js`

### 🎨 Feedback Visual Melhorado
- **🔄 Indicadores de Ação**:
  - `📝 Editando: app.py` (arquivo existente)
  - `📄 Criando: fibonacci.py` (arquivo novo)
  - `⚠️ arquivo.py já existe - será editado`

## [0.4.4] - 2024-01-XX

### Adicionado
- **🔍 Modo Debug**: Comando `/debug` para ativar/desativar exibição de respostas completas do LLM
- **📊 Diagnóstico Inteligente**: Sistema detecta quando LLM não usa tags estruturadas e informa ao usuário
- **💡 Dicas Contextuais**: Sugestões automáticas para melhorar comandos e obter ações automáticas

### Melhorado
- **📝 Instruções para LLM**: Instruções mais claras e mandatórias para uso de tags estruturadas
- **🔄 Ordem de Processamento**: Tags especiais são processadas ANTES da exibição do texto
- **⚡ Feedback Visual**: Indicadores claros quando código/ações são detectados e processados
- **🛠️ Debug Melhorado**: Preview de resposta quando tags não são encontradas

### Instruções Otimizadas
- **SEMPRE usar `<code filename="">` para criar arquivos**
- **SEMPRE usar `<actions>` para comandos shell**
- **SEMPRE usar `<read>` para examinar arquivos**
- **NUNCA usar ``` para criação de arquivos (apenas para exemplos)**

## [0.4.3] - 2024-01-XX

### Corrigido
- **🎯 Diretório de Criação de Arquivos**: Arquivos agora são criados no diretório correto onde o `xandai` foi iniciado
- **Comando `/file`**: Todas as operações (create, edit, append, delete, read, list) agora usam o diretório correto
- **Tags `<code>`**: Arquivos criados pelas tags especiais respeitam o working directory
- **Blocos de código tradicionais**: Compatibilidade com ``` também corrigida para usar diretório correto

## [0.4.2] - 2024-01-XX

### Adicionado
- **Tags de Ação Estruturadas**: Sistema de tags para organizar respostas do LLM
  - `<actions>` - Para comandos shell/terminal (executados automaticamente)
  - `<read>` - Para examinar arquivos existentes (executados automaticamente)  
  - `<code filename="nome.ext">` - Para criar arquivos automaticamente
- **Execução Automática Inteligente**: Scripts são executados diretamente em vez de criar arquivos .txt
- **Instruções Claras para LLM**: Prompt enhancer agora instrui o modelo sobre estrutura de resposta
- **Resposta Limpa**: Tags especiais são removidas da exibição (processadas separadamente)

### Melhorado
- **Processamento de Código**: Agora processa tanto tags especiais quanto blocos ``` (compatibilidade)
- **Detecção de Ações**: Comandos shell são identificados e executados automaticamente
- **Criação de Arquivos**: Processo mais direto e automático

## [0.4.1] - 2024-01-XX

### Corrigido
- **Comando `/task`**: Agora recebe corretamente os argumentos da tarefa complexa
- **Autocompletar**: Inclui todos os comandos disponíveis automaticamente

## [0.4.0] - 2024-01-XX

### Adicionado
- **Modo de Tarefa Complexa**: Comando `/task` para dividir projetos grandes em sub-tarefas
- **Task Manager**: Sistema inteligente para análise e execução sequencial de tarefas
- **Detecção de tipo de tarefa**: Identifica se é código, shell, texto ou misto
- **Progresso visual**: Mostra status de cada tarefa (pendente, em progresso, completa)
- **Contexto entre tarefas**: Tarefas posteriores têm conhecimento das anteriores
- **Formatação específica**: Texto puro é exibido formatado, código é processado normalmente

### Melhorado
- Prompts de tarefas incluem contexto e instruções específicas
- Melhor organização para projetos complexos
- Experiência mais guiada para tarefas grandes

## [0.3.0] - 2024-01-XX

### Adicionado
- **Detecção e suporte multi-plataforma**: Detecta Windows, macOS ou Linux automaticamente
- **Conversão automática de comandos**: Converte comandos Unix para Windows e vice-versa
- **Informação do OS no contexto**: Modelo recebe informação sobre o sistema operacional
- **Comandos específicos do OS**: Usa comandos apropriados (dir vs ls, type vs cat, etc.)

### Melhorado
- Banner mostra sistema operacional detectado
- Comandos em blocos de código são convertidos antes de executar
- Instruções específicas ao modelo baseadas no OS
- Melhor tratamento de encoding no Windows

### Corrigido
- Comandos Unix como `touch` agora funcionam no Windows (convertidos para equivalentes)
- Evita erros de "comando não reconhecido" em diferentes plataformas

## [0.2.2] - 2024-01-XX

### Corrigido
- **Diretório de trabalho correto**: Agora executa comandos no diretório onde o XandAI foi iniciado
- **Execução real de comandos**: Comandos como "list files" agora executam `dir`/`ls` real ao invés do modelo inventar resultados
- **Detecção inteligente de comandos**: Detecta quando o usuário quer listar arquivos e executa automaticamente

### Melhorado
- Banner mostra o diretório atual de trabalho
- Mais padrões de detecção para comandos diretos (where am i, current directory, etc.)
- Instruções ao modelo para não inventar saídas de comandos

## [0.2.1] - 2024-01-XX

### Melhorado
- **Interface mais limpa**: Removida saída excessiva durante geração de resposta
- **Execução automática de bash**: Comandos shell em blocos de código são executados automaticamente
- **Nomeação automática de arquivos**: Arquivos são nomeados automaticamente baseado no contexto
- **Detecção de comandos perigosos**: Pede confirmação antes de executar comandos destrutivos
- **Status dinâmico**: Mostra "Pensando...", "Escrevendo código...", etc. ao invés de imprimir toda a resposta

### Mudanças
- Agora mostra apenas indicadores de progresso durante a geração (não imprime chunk por chunk)
- Comandos bash/shell em blocos de código são executados silenciosamente
- Pergunta apenas "Salvar código? (s/N)" ao invés de pedir nome do arquivo
- Gera nomes inteligentes baseados no contexto (server.py, auth.js, test.go, etc.)
- Formatação melhorada da resposta com syntax highlighting inline

## [0.2.0] - 2024-01-XX

### Adicionado
- **Execução Automática de Comandos Shell**: Comandos shell comuns agora são detectados e executados automaticamente
  - Suporta comandos como `ls`, `cd`, `mkdir`, `git`, `npm`, `pip`, etc.
  - Detecta pipes (`|`) e redirecionamentos (`>`, `>>`)
  - Mantém o diretório atual entre comandos
  - Pode ser desativado com `/shell`

- **Melhoria Automática de Prompts**: Prompts são enriquecidos com contexto antes de serem enviados ao modelo
  - Extrai referências a arquivos automaticamente
  - Adiciona tags `<task>` para instruções claras
  - Detecta linguagem de programação e framework mencionados
  - Inclui contexto do diretório atual
  - Mantém histórico de contexto entre interações
  - Pode ser desativado com `/enhance`

- **Novos Comandos**:
  - `/shell` - Alterna execução automática de comandos shell
  - `/enhance` - Alterna melhoria automática de prompts

### Melhorado
- Detecção mais inteligente de tarefas de codificação
- Suporte expandido para conjugações de verbos em português
- Banner de boas-vindas mostra status das funcionalidades automáticas
- Documentação de ajuda atualizada com exemplos das novas funcionalidades

## [0.1.0] - 2024-01-XX

### Inicial
- Interface CLI interativa com OLLAMA
- Seleção visual de modelos disponíveis
- Operações de arquivo (criar, editar, ler, deletar, listar)
- Detecção e salvamento automático de blocos de código
- Syntax highlighting para várias linguagens
- Histórico persistente de comandos
- Autocompletar de comandos
- Confirmações de segurança para operações destrutivas
- Scripts de instalação para Windows e Unix
- Testes unitários e documentação completa
