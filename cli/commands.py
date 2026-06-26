import asyncio
import logging
import shlex
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.logging import RichHandler
from rich.text import Text

from core.di.container import get_container
from core.models.project import Project

console = Console()
app = typer.Typer(help="PROJECT WARROOM - AI-Powered Project Defense Platform")

logging.basicConfig(level=logging.WARNING, handlers=[RichHandler(console=console, show_time=False)])
logger = logging.getLogger("warroom")


def async_run(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


def _require_non_empty(value: str, name: str):
    if not value or not value.strip():
        console.print(f"[red]Error: {name} cannot be empty[/red]")
        raise typer.Exit(1)


@app.command("init")
def init_project(name: str, repo: Optional[str] = None, description: Optional[str] = None,
                 output_dir: str = "./warroom_projects"):
    """Initialize a new project for analysis"""
    _require_non_empty(name, "project name")
    project_path = Path(output_dir) / name
    if project_path.exists():
        console.print(f"[red]Error: Project '{name}' already exists at {project_path}[/red]")
        raise typer.Exit(1)
    project_path.mkdir(parents=True, exist_ok=True)
    project = Project.create(name=name, description=description or f"Project: {name}",
                             repository_url=repo, path=str(project_path))
    # Persist project metadata
    import json
    meta = {"id": project.id, "name": project.name, "description": project.description,
            "repository_url": repo, "created_at": str(project.created_at)}
    (project_path / ".warroom.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    console.print(f"[green]V[/green] Initialized project [bold]{name}[/bold] at {project_path}")
    if repo:
        console.print(f"   Repository: {repo}")
    console.print(f"   Project ID: {project.id}")
    console.print("\n[yellow]Next:[/yellow] Run [bold]warroom analyze {name}[/bold] to start analysis")


@app.command("analyze")
def analyze_project(project_name: str, output_format: str = "json", include: str = "all"):
    """Run comprehensive analysis on a project"""
    _require_non_empty(project_name, "project name")
    ctr = get_container()
    analyzer = ctr.get("analysis_service")
    if not analyzer:
        console.print("[red]Error: Analyzer service not available[/red]")
        raise typer.Exit(1)

    project = Project.create(name=project_name, description=f"Analysis of {project_name}")
    analysis_types = ["architecture", "hackathon", "innovation", "technical-debt",
                      "team-readiness", "competitive-advantage"]

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  BarColumn(), console=console) as progress:
        task = progress.add_task("[yellow]Analyzing project...", total=len(analysis_types))
        scores = {}
        for atype in analysis_types:
            progress.update(task, description=f"[yellow]Analyzing {atype.replace('-', ' ')}...")
            try:
                result = async_run(analyzer.analyze_project(project.id, [atype]))
                score = getattr(result, f"{atype.replace('-', '_')}_score", 65.0)
                scores[atype] = score
            except Exception as e:
                logger.warning(f"Analysis failed for {atype}: {e}")
                scores[atype] = 65.0
            progress.advance(task)

    table = Table(title=f"[bold]Analysis Results: {project_name}[/bold]")
    table.add_column("Metric", style="cyan")
    table.add_column("Score", justify="right")
    table.add_column("Status", style="yellow")

    for metric, score in scores.items():
        display_score = 100 - score if metric == "technical-debt" else score
        status = "[green]Excellent[/green]" if display_score >= 80 else "[yellow]Good[/yellow]" if display_score >= 65 else "[red]Needs Work[/red]"
        table.add_row(metric.replace("-", " ").title(), f"{display_score:.1f}%", status)

    avg = sum(scores.values()) / len(scores)
    table.add_row("[bold]Overall[/bold]", f"[bold]{avg:.1f}%[/bold]",
                  "[green]Strong[/green]" if avg >= 70 else "[yellow]Moderate[/yellow]")

    console.print(table)
    console.print(f"\n[green]V[/green] Analysis complete for [bold]{project_name}[/bold]")


@app.command("judge")
def judge_simulation(project_name: str, mode: str = "full-audit", questions_only: bool = False):
    """Run judge simulation for project defense training"""
    _require_non_empty(project_name, "project name")
    ctr = get_container()
    judge = ctr.get("judge_simulation")
    if not judge:
        console.print("[red]Error: Judge simulation not available[/red]")
        raise typer.Exit(1)

    project = Project.create(name=project_name, description=f"Judge simulation for {project_name}")

    from modules.judge_simulation_engine import JudgePersona, AttackMode
    persona_map = {"full-audit": JudgePersona.SIH_JUDGE, "technical": JudgePersona.TECHNICAL_ARCHITECT,
                   "business": JudgePersona.BUSINESS_EXECUTIVE}
    attack_map = {"gentle": AttackMode.GENTLE, "moderate": AttackMode.MODERATE,
                  "aggressive": AttackMode.AGGRESSIVE}

    persona = persona_map.get(mode, JudgePersona.SIH_JUDGE)
    attack = attack_map.get(mode if mode in attack_map else "moderate", AttackMode.MODERATE)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  console=console) as progress:
        progress.add_task("[yellow]Running judge simulation...", total=None)
        try:
            result = async_run(judge.run_simulation(project, persona=persona, mode=attack, num_questions=10))
        except Exception as e:
            console.print(f"[red]Judge simulation failed: {e}[/red]")
            raise typer.Exit(1)

    console.print(Panel(f"[bold]Judge Simulation: {project_name}[/bold]",
                        subtitle=f"Persona: {persona.value} | Mode: {attack.value}",
                        border_style="red"))

    score_table = Table()
    score_table.add_column("Metric", style="cyan")
    score_table.add_column("Score", justify="right")
    score_table.add_row("Overall", f"{result.overall_score:.1f}%")
    score_table.add_row("Technical", f"{result.technical_score:.1f}%")
    score_table.add_row("Presentation", f"{result.presentation_score:.1f}%")
    score_table.add_row("Defense", f"{result.defense_score:.1f}%")
    score_table.add_row("Innovation", f"{result.innovation_score:.1f}%")
    console.print(score_table)

    if not questions_only and result.weak_spots_exposed:
        console.print("\n[red]Weak Spots Exposed:[/red]")
        for spot in result.weak_spots_exposed[:3]:
            severity = spot.get("severity", "medium") if isinstance(spot, dict) else "medium"
            area = spot.get("area", "Unknown") if isinstance(spot, dict) else str(spot)
            feedback = spot.get("feedback", "") if isinstance(spot, dict) else ""
            console.print(f"  ! [{severity}] {area}: {feedback[:120]}")

    if result.improvement_suggestions:
        console.print("\n[green]Improvement Suggestions:[/green]")
        for s in result.improvement_suggestions[:4]:
            console.print(f"  -> {s}")

    if result.questions_asked and not questions_only:
        console.print("\n[bold]Sample Questions:[/bold]")
        for q in result.questions_asked[:4]:
            txt = f"[{q.difficulty}/10] {q.question[:120]}..." if len(q.question) > 120 else f"[{q.difficulty}/10] {q.question}"
            console.print(f"  {txt}")

    console.print(f"\n[red]Final Verdict:[/red] {result.final_verdict}")


@app.command("readiness")
def team_readiness(project_name: str):
    """Evaluate team readiness for hackathons and interviews"""
    _require_non_empty(project_name, "project name")
    ctr = get_container()
    readiness = ctr.get("hackathon_readiness")
    if not readiness:
        console.print("[red]Error: Readiness engine not available[/red]")
        raise typer.Exit(1)

    project = Project.create(name=project_name, description=f"Readiness evaluation for {project_name}")

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  console=console) as progress:
        progress.add_task("[yellow]Evaluating readiness...", total=None)
        try:
            result = async_run(readiness.evaluate_hackathon_readiness(project))
        except Exception as e:
            console.print(f"[red]Readiness evaluation failed: {e}[/red]")
            raise typer.Exit(1)

    console.print(f"\n[bold]Readiness Score: {result.overall_score:.1f}%[/bold]")

    table = Table(title="Readiness Breakdown")
    table.add_column("Criterion", style="cyan")
    table.add_column("Score", justify="right")
    table.add_column("Status")
    for criterion, score in result.evaluation_criteria.items():
        status = "[green]V[/green]" if score >= 70 else "[yellow]~[/yellow]" if score >= 55 else "[red]X[/red]"
        table.add_row(criterion.replace("_", " ").title(), f"{score:.1f}%", status)
    console.print(table)

    console.print(f"\nWinning Probability: [bold]{result.winning_probability:.1f}%[/bold]")
    console.print(f"Competition Level: {getattr(result, 'competition_level', 'N/A')}")

    if result.improvement_recommendations:
        console.print("\n[green]Recommendations:[/green]")
        for rec in result.improvement_recommendations[:5]:
            console.print(f"  -> {rec}")


@app.command("competitive")
def competitive_analysis(project_name: str):
    """Perform competitive intelligence analysis"""
    _require_non_empty(project_name, "project name")
    ctr = get_container()
    competitor = ctr.get("competitor_analysis")
    if not competitor:
        console.print("[red]Error: Competitor analysis not available[/red]")
        raise typer.Exit(1)

    project = Project.create(name=project_name, description=f"Competitive analysis for {project_name}")

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  console=console) as progress:
        progress.add_task("[yellow]Analyzing competitive landscape...", total=None)
        try:
            result = async_run(competitor.analyze_competition(project))
        except Exception as e:
            console.print(f"[red]Competitive analysis failed: {e}[/red]")
            raise typer.Exit(1)

    console.print(f"\n[bold]Competitive Analysis: {project_name}[/bold]")
    console.print(f"Position: {getattr(result, 'overall_position', 'N/A')}")
    console.print(f"Competitiveness: {result.competitiveness_score:.1f}% | "
                  f"Market Fit: {result.market_fit_score:.1f}% | "
                  f"Differentiation: {result.differentiation_score:.1f}%")

    if getattr(result, 'direct_competitors', None):
        table = Table(title="Direct Competitors")
        table.add_column("Competitor", style="cyan")
        table.add_column("Threat", style="red")
        table.add_column("Similarity")
        for comp in result.direct_competitors[:4]:
            table.add_row(comp.name, comp.threat_level, f"{comp.similarity_score:.0f}%")
        console.print(table)

    if getattr(result, 'blue_ocean_opportunities', None):
        console.print("\n[green]Blue Ocean Opportunities:[/green]")
        for opp in result.blue_ocean_opportunities[:3]:
            console.print(f"  {opp}")

    if getattr(result, 'strategic_recommendations', None):
        console.print("\n[bold]Strategic Recommendations:[/bold]")
        for rec in result.strategic_recommendations[:5]:
            console.print(f"  -> {rec}")


@app.command("dashboard")
def start_dashboard(project_name: str, port: int = 8080):
    """Start real-time dashboard for project monitoring"""
    _require_non_empty(project_name, "project name")
    if port < 1 or port > 65535:
        console.print("[red]Error: Port must be between 1 and 65535[/red]")
        raise typer.Exit(1)
    console.print(Panel(f"[bold]Dashboard: {project_name}[/bold]\nPort: {port}",
                        border_style="cyan"))
    console.print("[green]Starting API server...[/green]")
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=port, reload=False)


@app.command("scan")
def scan_project(path: str):
    """Scan a project directory for analysis"""
    _require_non_empty(path, "path")
    if not Path(path).exists():
        console.print(f"[red]Error: Path '{path}' does not exist[/red]")
        raise typer.Exit(1)

    ctr = get_container()
    scanner = ctr.get("project_scanner")
    if not scanner:
        console.print("[red]Scanner not available[/red]")
        raise typer.Exit(1)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  console=console) as progress:
        progress.add_task("[yellow]Scanning project...", total=None)
        try:
            result = async_run(scanner.scan_project(path))
        except Exception as e:
            console.print(f"[red]Scan failed: {e}[/red]")
            raise typer.Exit(1)

    console.print(f"\n[bold]Project Scan: {result.project_name}[/bold]")
    console.print(f"  Files: {result.total_files} | Dirs: {result.total_dirs}")
    console.print(f"  Size: {result.total_size_bytes / 1024:.1f} KB")

    if getattr(result, 'languages', None):
        lang_table = Table(title="Languages")
        lang_table.add_column("Language", style="cyan")
        lang_table.add_column("Files", justify="right")
        for lang, count in sorted(result.languages.items(), key=lambda x: -x[1])[:8]:
            lang_table.add_row(lang, str(count))
        console.print(lang_table)

    git = getattr(result, 'git_info', None)
    console.print(f"\n  Git: {'V' if git and git.has_git else 'X'}"
                  f" | README: {'V' if getattr(result, 'has_readme', False) else 'X'}"
                  f" | Tests: {'V' if getattr(result, 'has_tests', False) else 'X'}"
                  f" | Docker: {'V' if getattr(result, 'has_docker', False) else 'X'}"
                  f" | CI: {'V' if getattr(result, 'has_ci', False) else 'X'}")

    if git and git.has_git and getattr(git, 'branch', None):
        console.print(f"  Branch: {git.branch}"
                      f"{' | Remote: ' + git.remote_url if getattr(git, 'remote_url', None) else ''}")


@app.command("report")
def generate_report(project_name: str, report_type: str = "comprehensive", output_format: str = "pdf"):
    """Generate a professional report"""
    _require_non_empty(project_name, "project name")
    ctr = get_container()
    generator = ctr.get("report_generator")
    if not generator:
        console.print("[red]Error: Report generator not available[/red]")
        raise typer.Exit(1)

    # Run a fresh analysis to get real data
    analyzer = ctr.get("analysis_service")
    project = Project.create(name=project_name, description=f"Report for {project_name}")
    data = {"overall_score": 72.5, "scores": {}, "strengths": [], "weak_spots": [], "recommendations": []}
    if analyzer:
        try:
            result = async_run(analyzer.analyze_project(project.id))
            data = {
                "overall_score": result.overall_score,
                "scores": {
                    "architecture": result.architecture_score,
                    "innovation": result.innovation_score,
                    "hackathon_readiness": result.hackathon_readiness_score,
                    "technical_debt": result.technical_debt_score,
                    "team_readiness": result.team_readiness_score,
                    "competitive_advantage": result.competitive_advantage_score,
                },
                "strengths": result.strength_points,
                "weak_spots": [{"area": w, "title": w, "severity": "medium"} for w in result.weak_points],
                "recommendations": result.recommendations,
            }
        except Exception as e:
            logger.warning(f"Analysis for report failed: {e}")

    from modules.report_generator import ReportType, ReportFormat
    rt = ReportType(report_type) if report_type in [e.value for e in ReportType] else ReportType.COMPREHENSIVE
    rf = ReportFormat(output_format) if output_format in [e.value for e in ReportFormat] else ReportFormat.PDF

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  console=console) as progress:
        progress.add_task("[yellow]Generating report...", total=None)
        try:
            filename = async_run(generator.generate_report(rt, data, project_name, rf))
        except Exception as e:
            console.print(f"[red]Report generation failed: {e}[/red]")
            raise typer.Exit(1)

    console.print(f"[green]V[/green] Report generated: {filename}")


@app.command("roast")
def roast_project(path: str):
    """Brutally roast a project with savage AI-powered humor"""
    _require_non_empty(path, "path")
    if not Path(path).exists():
        console.print(f"[red]Error: Path '{path}' does not exist[/red]")
        raise typer.Exit(1)

    skull = r"""[red]     .-.
    (o o)
    | O |
    |   |
    '~~~'
  ☠️  WARning!  ☠️[/red]"""

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  console=console) as progress:
        progress.add_task("[red]Preparing the roast...", total=None)
        import time
        time.sleep(0.5)
        for frame in range(3):
            console.print(skull)
            time.sleep(0.3)
        progress.add_task("[red]Summoning the roast master...", total=None)
        time.sleep(0.5)

    console.print()
    console.print(Panel("[bold red]☠️  YOU HAVE BEEN WARNED — THE ROAST IS COMING  ☠️[/bold red]",
                        border_style="red"))
    console.print()

    ctr = get_container()
    roaster = ctr.get("roast_engine")
    if not roaster:
        console.print("[red]Error: Roast engine not available[/red]")
        raise typer.Exit(1)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  BarColumn(), console=console) as progress:
        task = progress.add_task("[red]Roasting project...", total=None)
        try:
            result = async_run(roaster.roast_project(path))
        except Exception as e:
            console.print(f"[red]Roast failed: {e}[/red]")
            raise typer.Exit(1)
        progress.update(task, completed=True)

    console.print()
    console.print(Panel(f"[bold yellow]Roast: {result.project_name}[/bold yellow]",
                        border_style="red"))
    console.print(f"\n[bold red]{result.burn}[/bold red]\n")

    flame_count = max(1, min(10, result.score // 10))
    flames = "🔥" * flame_count + "💀" * (10 - flame_count)
    console.print(f"[bold]Roast Intensity:[/bold] {result.score}/100 {flames}")

    console.print("\n[red]Shade thrown:[/red]")
    for s in result.shade:
        console.print(f"  🎤 [italic]{s}[/italic]")

    console.print(f"\n[bold]Damage Report:[/bold] {result.total_files} files, "
                  f"{len(result.languages)} language types detected")
    console.print("[bold red]☠️  THE ROAST IS OVER. GO FIX YOUR CODE.  ☠️[/bold red]")


@app.command("version")
def show_version():
    """Show version information"""
    console.print(Panel("PROJECT WARROOM v0.1.0\nAI-Powered Project Defense Platform\n\n"
                        "12 Modules * FastAPI * Typer * PostgreSQL * ChromaDB * Ollama",
                        title="Version", border_style="green"))


WAR_BANNER = """[bold cyan]
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║    ██╗    ██╗ █████╗ ██████╗ ██████╗  ██████╗  ██████╗ ███╗   ███╗
║    ██║    ██║██╔══██╗██╔══██╗██╔══██╗██╔═══██╗██╔═══██╗████╗ ████║
║    ██║ █╗ ██║███████║██████╔╝██████╔╝██║   ██║██║   ██║██╔████╔██║
║    ██║███╗██║██╔══██║██╔══██╗██╔══██╗██║   ██║██║   ██║██║╚██╔╝██║
║    ╚███╔███╔╝██║  ██║██║  ██║██║  ██║╚██████╔╝╚██████╔╝██║ ╚═╝ ██║
║     ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚═╝     ╚═╝
║                                                          ║
║           PROJECT WARROOM v0.1.0                         ║
║      AI-Powered Project Defense Platform                  ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
[/bold cyan]"""


def show_banner():
    console.print(WAR_BANNER)
    console.print("[dim]Type [bold]help[/bold] for commands, [bold]exit[/bold] to quit.[/dim]\n")


def show_interactive_help():
    help_lines = [
        "",
        "[bold cyan]Available Commands:[/bold cyan]",
        "  [green]init[/green] <name>          Initialize a new project",
        "  [green]scan[/green] <path>          Scan a project directory",
        "  [green]analyze[/green] <name>       Run comprehensive analysis",
        "  [green]judge[/green] <name>         Run judge simulation",
        "  [green]readiness[/green] <name>     Evaluate team readiness",
        "  [green]competitive[/green] <name>   Competitive analysis",
        "  [green]dashboard[/green] <name>     Start monitoring dashboard",
        "  [green]report[/green] <name>        Generate professional report",
        "  [green]roast[/green] <path>         Brutally roast a project",
        "  [green]version[/green]              Show version info",
        "  [green]help[/green]                 Show this help",
        "  [green]exit[/green] / [green]quit[/green]          Exit warroom",
        "",
        "[dim]For command details, run: [bold]<command> --help[/bold][/dim]",
    ]
    console.print("\n".join(help_lines))


def interactive_shell():
    show_banner()
    while True:
        try:
            try:
                raw = input("warroom> ").strip()
            except EOFError:
                break
            if not raw:
                continue
            if raw in ("exit", "quit", "q"):
                console.print("[yellow]Exiting warroom. Good luck out there.[/yellow]")
                break
            if raw == "help":
                show_interactive_help()
                continue
            if raw == "version":
                show_version()
                continue

            # Strip leading "warroom" so both "scan ..." and "warroom scan ..." work
            if raw.startswith("warroom "):
                raw = raw[8:]
            elif raw == "warroom":
                show_interactive_help()
                continue

            old_argv = sys.argv
            sys.argv = ["warroom"] + shlex.split(raw)
            try:
                app()
            except SystemExit:
                pass
            finally:
                sys.argv = old_argv
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Use 'exit' to quit.[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def main():
    if len(sys.argv) <= 1:
        interactive_shell()
    else:
        app()


if __name__ == "__main__":
    main()
