"""
Main entry point for XandAI
"""

import click
from .cli import XandAICLI
from .api import OllamaAPIError
from rich.console import Console

console = Console()


@click.command()
@click.option(
    '--endpoint',
    '-e',
    default='http://localhost:11434',
    help='OLLAMA API endpoint (default: http://localhost:11434)'
)
@click.version_option(version='0.5.3', prog_name='XandAI')
def main(endpoint: str):
    """
    XandAI - Interactive CLI assistant for OLLAMA models
    
    This tool allows interaction with language models through the OLLAMA API,
    with extended capabilities to create, edit and delete files.
    """
    try:
        cli = XandAICLI(endpoint=endpoint)
        cli.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user.[/yellow]")
    except OllamaAPIError as e:
        console.print(f"\n[red]API error: {e}[/red]")
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {e}[/red]")
        console.print("[dim]For more details, run with --debug[/dim]")


if __name__ == '__main__':
    main()
