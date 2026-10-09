"""Command-line interface (CLI) entry point for the AI Coding Agent."""

import argparse
import os
import sys
from pathlib import Path

from config import Config, default_config
from agent.agent import CodingAgent
from agent.llm import get_llm_client, MockLLMClient, OpenAILLMClient

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.syntax import Syntax
    from rich.markdown import Markdown
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False
    console = None


def print_header():
    title = "AI CODING ASSISTANT"
    subtitle = "Autonomous Repository Engineer & Debugger"
    if HAS_RICH:
        console.print(Panel.fit(f"[bold cyan]{title}[/bold cyan]\n[dim]{subtitle}[/dim]", border_style="cyan"))
    else:
        print("=" * 60)
        print(f" {title} - {subtitle} ".center(60, "="))
        print("=" * 60)


def display_repo_info(repo_info):
    if HAS_RICH:
        table = Table(title="Repository Overview", border_style="blue", show_header=True)
        table.add_column("Property", style="bold yellow")
        table.add_column("Details", style="white")

        table.add_row("Name", repo_info.name)
        table.add_row("Location", repo_info.path)
        table.add_row("Git Branch", repo_info.git_branch or "N/A (Not a git repo)")
        table.add_row("Languages", ", ".join(repo_info.languages) or "Undetermined")
        table.add_row("Package Managers", ", ".join(repo_info.package_managers) or "None detected")
        table.add_row("Build Systems", ", ".join(repo_info.build_systems) or "None detected")
        table.add_row("Test Runners", ", ".join(repo_info.test_runners) or "None detected")
        table.add_row("Total Files", str(repo_info.file_count))
        console.print(table)
    else:
        print("\n--- Repository Overview ---")
        print(f"Name: {repo_info.name}")
        print(f"Path: {repo_info.path}")
        print(f"Branch: {repo_info.git_branch or 'N/A'}")
        print(f"Languages: {', '.join(repo_info.languages)}")
        print(f"Test Runners: {', '.join(repo_info.test_runners)}")
        print(f"Total Files: {repo_info.file_count}\n")


def display_agent_result(result):
    if HAS_RICH:
        status_color = "bold green" if result.success else "bold red"
        status_text = "SUCCESSFUL" if result.success else "FAILED / INCOMPLETE"

        console.print(Panel(f"[{status_color}]Task Status: {status_text}[/{status_color}]\n\n{result.final_summary}", title="Execution Report", border_style="green" if result.success else "red"))

        if result.diff_summary:
            console.print("\n[bold yellow]Unified Diff of Changes Applied:[/bold yellow]")
            clean_diff = result.diff_summary.replace("\ufeff", "")
            try:
                syntax = Syntax(clean_diff, "diff", theme="monokai", line_numbers=True)
                console.print(syntax)
            except Exception:
                print(clean_diff)

        if result.tests_executed:
            table = Table(title="Test Verification History", border_style="magenta")
            table.add_column("Run", style="cyan")
            table.add_column("Command", style="white")
            table.add_column("Passed", style="green")
            table.add_column("Failed", style="red")
            table.add_column("Status", style="bold")

            for idx, tr in enumerate(result.tests_executed, 1):
                status = "[green]PASSED[/green]" if tr.is_success else "[red]FAILED[/red]"
                table.add_row(f"Run {idx}", tr.command, str(tr.passed), str(tr.failed), status)
            console.print(table)
    else:
        print("\n" + "=" * 60)
        print(" execution report ".upper().center(60, "="))
        print("=" * 60)
        print(result.final_summary)
        if result.diff_summary:
            print("\nUnified Diff:")
            print(result.diff_summary)
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Autonomous AI Coding Agent capable of inspecting repos, planning, modifying code, and debugging.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo", "-r", type=str, default=".", help="Repository path or GitHub URL to inspect and work on")
    parser.add_argument("--task", "-t", type=str, help="Coding task or bug fix instruction")
    parser.add_argument("--auto-approve", "-y", action="store_true", help="Automatically approve plans without interactive prompt")
    parser.add_argument("--provider", type=str, default=None, help="LLM provider: openai, mock, etc.")
    parser.add_argument("--model", "-m", type=str, default=None, help="LLM model name (e.g. gpt-4o-mini)")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run interactive prompt session")

    args = parser.parse_args()

    print_header()

    # Configure agent
    cfg = Config()
    if args.auto_approve:
        cfg.auto_approve = True
    if args.provider:
        cfg.llm_provider = args.provider
    if args.model:
        cfg.llm_model = args.model

    # Status message logger
    def status_callback(msg: str):
        if HAS_RICH:
            console.print(f"[bold blue]>[/bold blue] {msg}")
        else:
            print(f"> {msg}")

    agent = CodingAgent(config=cfg, status_callback=status_callback)

    # Step 1-4: Load and scan repo
    try:
        repo_info = agent.load_repository(args.repo)
        display_repo_info(repo_info)
    except Exception as e:
        if HAS_RICH:
            console.print(f"[bold red]Error opening repository:[/bold red] {e}")
        else:
            print(f"Error opening repository: {e}")
        sys.exit(1)

    # Determine task
    task = args.task
    if not task:
        if args.interactive or not sys.stdin.isatty():
            prompt_str = "\nEnter coding task (or 'exit' to quit): "
            try:
                task = input(prompt_str).strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting.")
                sys.exit(0)
        else:
            task = input("\nEnter coding task description: ").strip()

    if not task or task.lower() in ("exit", "quit"):
        print("No task provided. Exiting.")
        sys.exit(0)

    # Run agent loop
    result = agent.run(repo_target=repo_info.path, task=task)
    display_agent_result(result)

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
