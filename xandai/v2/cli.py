"""
Interface CLI principal do XandAI - Versão Refatorada
Importa e utiliza a estrutura modular do pacote cli/
"""

from .cli import XandAICLI


def main():
    """Main entry point for the CLI"""
    cli = XandAICLI()
    cli.run()


if __name__ == "__main__":
    main()
