"""CLI entry point for prompt expansion pipeline."""

from pathlib import Path
from typing import Optional

import anthropic
import click
import pyperclip
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from .phases import classify_prompt, expand_prompt, restyle_content
from .style import get_default_style_profile, parse_style_file

console = Console()


@click.command()
@click.argument("prompt", required=False)
@click.option(
    "--style-profile",
    "-s",
    type=click.Path(exists=True, path_type=Path),
    help="Path to custom style profile markdown file.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file for final restyled content.",
)
@click.option(
    "--no-clipboard",
    is_flag=True,
    help="Don't copy expanded prompt to clipboard.",
)
def main(
    prompt: Optional[str],
    style_profile: Optional[Path],
    output: Optional[Path],
    no_clipboard: bool,
) -> None:
    """Expand a rough prompt and restyle the output.

    Takes a rough prompt, classifies it, expands it into a structured format,
    then restyles the Claude web UI response to match Daniel's writing style.

    \b
    Examples:
        prompt-expand "How do attention mechanisms work?"
        prompt-expand --style-profile custom.md "Write about AI safety"
        prompt-expand  # interactive mode
    """
    # Initialize Anthropic client
    try:
        client = anthropic.Anthropic()
    except anthropic.AuthenticationError:
        console.print(
            "[red]Error: ANTHROPIC_API_KEY not set or invalid.[/red]\n"
            "Set it with: export ANTHROPIC_API_KEY=your-key"
        )
        raise SystemExit(1)

    # Load style profile
    if style_profile:
        profile = parse_style_file(style_profile)
        console.print(f"[dim]Using style profile: {style_profile}[/dim]")
    else:
        profile = get_default_style_profile()
        console.print("[dim]Using default style profile (Daniel Langkilde)[/dim]")

    # Get prompt if not provided
    if not prompt:
        console.print("\n[bold]Enter your rough prompt:[/bold]")
        prompt = Prompt.ask("", default="")
        if not prompt.strip():
            console.print("[yellow]No prompt provided. Exiting.[/yellow]")
            raise SystemExit(0)

    console.print()

    # Phase 1: Classify
    with console.status("[bold blue]Classifying prompt...[/bold blue]"):
        classification = classify_prompt(prompt, client)

    console.print(
        Panel(
            f"[bold]Category:[/bold] {classification.category.value}\n"
            f"[bold]Confidence:[/bold] {classification.confidence:.0%}\n"
            f"[bold]Reasoning:[/bold] {classification.reasoning}",
            title="[cyan]Classification[/cyan]",
            border_style="cyan",
        )
    )

    # Phase 2: Expand
    with console.status("[bold blue]Expanding prompt...[/bold blue]"):
        expanded = expand_prompt(prompt, classification, client)

    full_prompt = expanded.to_full_prompt()

    console.print("\n[green]── Expanded Prompt ──[/green]\n")
    console.print(full_prompt)
    console.print("\n[green]── End ──[/green]")

    # Copy to clipboard
    if not no_clipboard:
        try:
            pyperclip.copy(full_prompt)
            console.print("[green]Expanded prompt copied to clipboard.[/green]")
        except pyperclip.PyperclipException:
            console.print("[yellow]Could not copy to clipboard.[/yellow]")

    console.print()
    console.print("[bold]Instructions:[/bold]")
    console.print("1. Paste the expanded prompt into Claude web UI")
    console.print("2. Get the response")
    console.print("3. Paste the response below when prompted")
    console.print()

    # Wait for user to paste response
    console.print("[bold]Paste the Claude web UI response below.[/bold]")
    console.print("[dim](Press Enter twice when done)[/dim]")

    lines = []
    empty_count = 0
    while True:
        try:
            line = input()
            if line == "":
                empty_count += 1
                if empty_count >= 2:
                    break
                lines.append(line)
            else:
                empty_count = 0
                lines.append(line)
        except EOFError:
            break

    response_content = "\n".join(lines).strip()

    if not response_content:
        console.print("[yellow]No response provided. Exiting.[/yellow]")
        raise SystemExit(0)

    console.print()

    # Phase 4: Restyle
    with console.status("[bold blue]Restyling content...[/bold blue]"):
        restyled = restyle_content(response_content, profile, client)

    console.print("\n[magenta]── Restyled Output ──[/magenta]\n")
    console.print(Markdown(restyled))
    console.print("\n[magenta]── End ──[/magenta]")

    # Save to file if requested
    if output:
        output.write_text(restyled)
        console.print(f"\n[green]Saved to {output}[/green]")

    # Copy restyled to clipboard
    if not no_clipboard:
        try:
            pyperclip.copy(restyled)
            console.print("[green]Restyled output copied to clipboard.[/green]")
        except pyperclip.PyperclipException:
            pass


if __name__ == "__main__":
    main()
