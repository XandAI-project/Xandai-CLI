# PowerShell script to install LSP servers for multiple languages
# Usage: .\scripts\install_lsp_servers.ps1 [language]
# If no language specified, prompts for selection

param(
    [Parameter(Position=0)]
    [string]$Language
)

Write-Host "XandAI LSP Server Installation Script" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if a command exists
function Test-Command {
    param($CommandName)
    $null -ne (Get-Command $CommandName -ErrorAction SilentlyContinue)
}

# Install Python LSP servers
function Install-Python {
    Write-Host "Installing Python LSP servers..." -ForegroundColor Yellow
    if (Test-Command pip) {
        pip install -r requirements-lsp.txt
        Write-Host "✓ Python LSP servers installed" -ForegroundColor Green
    } else {
        Write-Host "✗ pip not found. Please install Python first." -ForegroundColor Red
        return $false
    }
    return $true
}

# Install JavaScript/TypeScript LSP server
function Install-JavaScript {
    Write-Host "Installing JavaScript/TypeScript LSP server..." -ForegroundColor Yellow
    if (Test-Command npm) {
        npm install -g typescript-language-server typescript
        Write-Host "✓ TypeScript Language Server installed" -ForegroundColor Green
    } else {
        Write-Host "✗ npm not found. Please install Node.js first." -ForegroundColor Red
        return $false
    }
    return $true
}

# Install Rust LSP server
function Install-Rust {
    Write-Host "Installing Rust LSP server..." -ForegroundColor Yellow
    if (Test-Command rustup) {
        rustup component add rust-analyzer
        Write-Host "✓ rust-analyzer installed" -ForegroundColor Green
    } else {
        Write-Host "✗ rustup not found. Please install Rust first." -ForegroundColor Red
        Write-Host "Visit: https://rustup.rs/" -ForegroundColor Yellow
        return $false
    }
    return $true
}

# Install Go LSP server
function Install-Go {
    Write-Host "Installing Go LSP server..." -ForegroundColor Yellow
    if (Test-Command go) {
        go install golang.org/x/tools/gopls@latest
        Write-Host "✓ gopls installed" -ForegroundColor Green
    } else {
        Write-Host "✗ go not found. Please install Go first." -ForegroundColor Red
        return $false
    }
    return $true
}

# Install Ruby LSP server
function Install-Ruby {
    Write-Host "Installing Ruby LSP server..." -ForegroundColor Yellow
    if (Test-Command gem) {
        gem install solargraph
        Write-Host "✓ Solargraph installed" -ForegroundColor Green
    } else {
        Write-Host "✗ gem not found. Please install Ruby first." -ForegroundColor Red
        return $false
    }
    return $true
}

# Install PHP LSP server
function Install-PHP {
    Write-Host "Installing PHP LSP server..." -ForegroundColor Yellow
    if (Test-Command npm) {
        npm install -g intelephense
        Write-Host "✓ Intelephense installed" -ForegroundColor Green
    } else {
        Write-Host "✗ npm not found. Please install Node.js first." -ForegroundColor Red
        return $false
    }
    return $true
}

# Install HTML/CSS/JSON LSP servers
function Install-Web {
    Write-Host "Installing HTML/CSS/JSON LSP servers..." -ForegroundColor Yellow
    if (Test-Command npm) {
        npm install -g vscode-langservers-extracted
        Write-Host "✓ Web language servers installed" -ForegroundColor Green
    } else {
        Write-Host "✗ npm not found. Please install Node.js first." -ForegroundColor Red
        return $false
    }
    return $true
}

# Install all available LSP servers
function Install-All {
    Write-Host "Installing all available LSP servers..." -ForegroundColor Yellow
    Write-Host ""

    Install-Python | Out-Null
    Write-Host ""
    Install-JavaScript | Out-Null
    Write-Host ""
    Install-Rust | Out-Null
    Write-Host ""
    Install-Go | Out-Null
    Write-Host ""
    Install-Ruby | Out-Null
    Write-Host ""
    Install-PHP | Out-Null
    Write-Host ""
    Install-Web | Out-Null

    Write-Host ""
    Write-Host "Installation complete!" -ForegroundColor Green
}

# Show menu
function Show-Menu {
    Write-Host "Select language(s) to install LSP servers for:"
    Write-Host ""
    Write-Host "  1) Python"
    Write-Host "  2) JavaScript/TypeScript"
    Write-Host "  3) Rust"
    Write-Host "  4) Go"
    Write-Host "  5) Ruby"
    Write-Host "  6) PHP"
    Write-Host "  7) HTML/CSS/JSON"
    Write-Host "  8) All available"
    Write-Host "  9) Exit"
    Write-Host ""

    $choice = Read-Host "Enter your choice [1-9]"

    switch ($choice) {
        "1" { Install-Python }
        "2" { Install-JavaScript }
        "3" { Install-Rust }
        "4" { Install-Go }
        "5" { Install-Ruby }
        "6" { Install-PHP }
        "7" { Install-Web }
        "8" { Install-All }
        "9" { exit 0 }
        default { Write-Host "Invalid choice" -ForegroundColor Red }
    }
}

# Main script
if ([string]::IsNullOrEmpty($Language)) {
    # No arguments, show menu
    Show-Menu
} else {
    # Install specific language
    switch ($Language.ToLower()) {
        {($_ -eq "python") -or ($_ -eq "py")} { Install-Python }
        {($_ -eq "javascript") -or ($_ -eq "js") -or ($_ -eq "typescript") -or ($_ -eq "ts")} { Install-JavaScript }
        {($_ -eq "rust") -or ($_ -eq "rs")} { Install-Rust }
        {($_ -eq "go") -or ($_ -eq "golang")} { Install-Go }
        {($_ -eq "ruby") -or ($_ -eq "rb")} { Install-Ruby }
        "php" { Install-PHP }
        {($_ -eq "web") -or ($_ -eq "html") -or ($_ -eq "css") -or ($_ -eq "json")} { Install-Web }
        "all" { Install-All }
        default {
            Write-Host "Unknown language: $Language" -ForegroundColor Red
            Write-Host "Usage: .\install_lsp_servers.ps1 [python|javascript|rust|go|ruby|php|web|all]"
            exit 1
        }
    }
}
