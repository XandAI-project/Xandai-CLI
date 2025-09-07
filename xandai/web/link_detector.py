"""
Link Detection and Validation

Detecta e valida links no texto do usuário, evitando
processar links em comandos shell, exemplos de código, etc.
"""

import re
from typing import List, Optional, Tuple
from urllib.parse import urlparse


class LinkDetector:
    """
    Detector inteligente de links com validação de contexto

    Evita processar links que aparecem em:
    - Comandos shell (git clone, curl, wget, etc.)
    - Exemplos de código
    - Strings literais
    - Comentários
    """

    # Padrões para detectar URLs
    URL_PATTERNS = [
        # HTTP/HTTPS URLs
        r'https?://[^\s<>"\'`|()]+',
        # URLs without protocol but with common TLDs
        r'(?:^|\s)(?:www\.)?[a-zA-Z0-9-]+\.(?:com|org|net|edu|gov|io|co|uk|de|fr|jp|cn|br|au|in|ca|ru|it|es|nl|se|no|dk|fi|pl|ch|at|be|cz|pt|gr|hu|ro|sk|bg|hr|si|ee|lv|lt|lu|mt|cy)\b[^\s<>"\'`|()]*',
    ]

    # Comandos que frequentemente contêm URLs que NÃO devem ser processados
    SHELL_COMMANDS = {
        "git",
        "curl",
        "wget",
        "npm",
        "pip",
        "docker",
        "ansible",
        "terraform",
        "helm",
        "kubectl",
        "aws",
        "gcloud",
        "az",
        "mvn",
        "gradle",
        "composer",
        "gem",
        "go",
        "cargo",
    }

    # Prefixos de contexto que indicam que links NÃO devem ser processados
    SKIP_CONTEXTS = [
        "git clone",
        "curl -",
        "wget ",
        "docker pull",
        "docker run",
        "npm install",
        "pip install",
        "apt install",
        "yum install",
        "Example:",
        "example:",
        "e.g.",
        "Ex:",
        "Usage:",
        "usage:",
        "$ ",
        "> ",
        "# ",
        "cmd>",
        "PS>",
        "powershell>",
        "bash>",
        "Run:",
        "run:",
        "Execute:",
        "execute:",
        "Command:",
        "command:",
    ]

    def __init__(self):
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.URL_PATTERNS
        ]

    def find_processable_links(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Encontra links que devem ser processados (não em comandos/exemplos)

        Args:
            text: Texto a ser analisado

        Returns:
            Lista de tuplas (url, start_pos, end_pos) para links válidos
        """
        all_links = self._find_all_links(text)
        processable_links = []

        for url, start, end in all_links:
            if self._should_process_link(text, url, start, end):
                processable_links.append((url, start, end))

        return processable_links

    def _find_all_links(self, text: str) -> List[Tuple[str, int, int]]:
        """Encontra todos os links no texto"""
        links = []

        for pattern in self.compiled_patterns:
            for match in pattern.finditer(text):
                url = match.group().strip()
                # Remove punctuation at the end
                url = re.sub(r"[.,;:!?\])}]+$", "", url)

                if self._is_valid_url(url):
                    links.append((url, match.start(), match.end()))

        # Remove duplicates and sort by position
        links = list(set(links))
        links.sort(key=lambda x: x[1])

        return links

    def _is_valid_url(self, url: str) -> bool:
        """Valida se uma string é um URL válido"""
        try:
            # Add protocol if missing
            if not url.startswith(("http://", "https://")):
                url = "http://" + url

            result = urlparse(url)
            return all(
                [
                    result.scheme in ("http", "https"),
                    result.netloc,
                    "." in result.netloc,  # Must have a domain
                    len(result.netloc) > 3,  # Minimum domain length
                ]
            )
        except Exception:
            return False

    def _should_process_link(self, text: str, url: str, start: int, end: int) -> bool:
        """
        Determina se um link deve ser processado baseado no contexto

        Args:
            text: Texto completo
            url: URL encontrada
            start: Posição inicial da URL
            end: Posição final da URL

        Returns:
            True se o link deve ser processado
        """
        # Get context around the link
        context_start = max(0, start - 50)
        context_end = min(len(text), end + 20)
        context = text[context_start:context_end].lower()

        # Check for skip contexts
        for skip_pattern in self.SKIP_CONTEXTS:
            if skip_pattern.lower() in context:
                return False

        # Check if it's part of a shell command
        line_start = text.rfind("\n", 0, start)
        line_start = line_start + 1 if line_start != -1 else 0

        line_content = text[line_start:start].strip().lower()

        # Check for shell command patterns
        words = line_content.split()
        if words:
            first_word = words[0].split("/")[-1]  # Handle paths like /usr/bin/git
            if first_word in self.SHELL_COMMANDS:
                return False

        # Check for code block indicators
        code_indicators = ["```", "`", "code:", "script:", "#!/"]
        for indicator in code_indicators:
            if indicator in context:
                return False

        # Check for quoted contexts
        quote_chars = ['"', "'", "`"]
        for quote in quote_chars:
            # Find quotes before and after the URL
            before_quote = text.rfind(quote, context_start, start)
            after_quote = text.find(quote, end, context_end)
            if before_quote != -1 and after_quote != -1:
                return False

        return True

    def normalize_url(self, url: str) -> str:
        """Normaliza URL adicionando protocolo se necessário"""
        if not url.startswith(("http://", "https://")):
            return "https://" + url
        return url
