#!/bin/bash
# Install LSP servers for multiple languages
# Usage: ./scripts/install_lsp_servers.sh [language]
# If no language specified, prompts for selection

set -e

echo "XandAI LSP Server Installation Script"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install Python LSP servers
install_python() {
    echo -e "${YELLOW}Installing Python LSP servers...${NC}"
    if command_exists pip; then
        pip install -r requirements-lsp.txt
        echo -e "${GREEN}✓ Python LSP servers installed${NC}"
    else
        echo -e "${RED}✗ pip not found. Please install Python first.${NC}"
        return 1
    fi
}

# Install JavaScript/TypeScript LSP server
install_javascript() {
    echo -e "${YELLOW}Installing JavaScript/TypeScript LSP server...${NC}"
    if command_exists npm; then
        npm install -g typescript-language-server typescript
        echo -e "${GREEN}✓ TypeScript Language Server installed${NC}"
    else
        echo -e "${RED}✗ npm not found. Please install Node.js first.${NC}"
        return 1
    fi
}

# Install Rust LSP server
install_rust() {
    echo -e "${YELLOW}Installing Rust LSP server...${NC}"
    if command_exists rustup; then
        rustup component add rust-analyzer
        echo -e "${GREEN}✓ rust-analyzer installed${NC}"
    else
        echo -e "${RED}✗ rustup not found. Please install Rust first.${NC}"
        echo -e "${YELLOW}Visit: https://rustup.rs/${NC}"
        return 1
    fi
}

# Install Go LSP server
install_go() {
    echo -e "${YELLOW}Installing Go LSP server...${NC}"
    if command_exists go; then
        go install golang.org/x/tools/gopls@latest
        echo -e "${GREEN}✓ gopls installed${NC}"
    else
        echo -e "${RED}✗ go not found. Please install Go first.${NC}"
        return 1
    fi
}

# Install Ruby LSP server
install_ruby() {
    echo -e "${YELLOW}Installing Ruby LSP server...${NC}"
    if command_exists gem; then
        gem install solargraph
        echo -e "${GREEN}✓ Solargraph installed${NC}"
    else
        echo -e "${RED}✗ gem not found. Please install Ruby first.${NC}"
        return 1
    fi
}

# Install PHP LSP server
install_php() {
    echo -e "${YELLOW}Installing PHP LSP server...${NC}"
    if command_exists npm; then
        npm install -g intelephense
        echo -e "${GREEN}✓ Intelephense installed${NC}"
    else
        echo -e "${RED}✗ npm not found. Please install Node.js first.${NC}"
        return 1
    fi
}

# Install HTML/CSS/JSON LSP servers
install_web() {
    echo -e "${YELLOW}Installing HTML/CSS/JSON LSP servers...${NC}"
    if command_exists npm; then
        npm install -g vscode-langservers-extracted
        echo -e "${GREEN}✓ Web language servers installed${NC}"
    else
        echo -e "${RED}✗ npm not found. Please install Node.js first.${NC}"
        return 1
    fi
}

# Install all available LSP servers
install_all() {
    echo -e "${YELLOW}Installing all available LSP servers...${NC}"
    echo ""

    install_python || true
    echo ""
    install_javascript || true
    echo ""
    install_rust || true
    echo ""
    install_go || true
    echo ""
    install_ruby || true
    echo ""
    install_php || true
    echo ""
    install_web || true

    echo ""
    echo -e "${GREEN}Installation complete!${NC}"
}

# Show menu
show_menu() {
    echo "Select language(s) to install LSP servers for:"
    echo ""
    echo "  1) Python"
    echo "  2) JavaScript/TypeScript"
    echo "  3) Rust"
    echo "  4) Go"
    echo "  5) Ruby"
    echo "  6) PHP"
    echo "  7) HTML/CSS/JSON"
    echo "  8) All available"
    echo "  9) Exit"
    echo ""
    read -p "Enter your choice [1-9]: " choice

    case $choice in
        1) install_python ;;
        2) install_javascript ;;
        3) install_rust ;;
        4) install_go ;;
        5) install_ruby ;;
        6) install_php ;;
        7) install_web ;;
        8) install_all ;;
        9) exit 0 ;;
        *) echo -e "${RED}Invalid choice${NC}" ;;
    esac
}

# Main script
if [ $# -eq 0 ]; then
    # No arguments, show menu
    show_menu
else
    # Install specific language
    case "$1" in
        python|py) install_python ;;
        javascript|js|typescript|ts) install_javascript ;;
        rust|rs) install_rust ;;
        go|golang) install_go ;;
        ruby|rb) install_ruby ;;
        php) install_php ;;
        web|html|css|json) install_web ;;
        all) install_all ;;
        *)
            echo -e "${RED}Unknown language: $1${NC}"
            echo "Usage: $0 [python|javascript|rust|go|ruby|php|web|all]"
            exit 1
            ;;
    esac
fi
