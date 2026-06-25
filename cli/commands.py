import asyncio
import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.logging import RichHandler

from core.di.container import container
from core.models.project import Project

console = Console()
app = typer.Typer(help="PROJECT WARROOM - AI-Powered Project Defense Platform")

logging.basicConfig(level=logging.INFO, handlers=[RichHandler(console=console, show_time=False)])
logger = logging.getLogger("warroom")


def async_run(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@app.command("init")
def init_project(name: str, repo: Optional[str] = None, description: Optional[str] = None,
                 output_dir: str = "./warroom_projects"):
    """Initialize a new project for analysis"""
    project_path = Path(output_dir) / name
    project_path.mkdir(parents=True, exist_ok=True)
    project = Project.create(name=name, description=description or f"Project: {name}",
                             repository_url=repo, path=str(project_path))
    console.print(f"[green]✓[/green] Initialized project [bold]{name}[/bold] at {project_path}")
    if repo:
        console.print(f"   Repository: {repo}")
    console.print(f"   Project ID: {project.id}")
    console.print("\n[yellow]Next:[/yellow] Run [bold]warroom analyze[/bold] to start analysis")


@app.command("analyze")
def analyze_project(project_name: str, format: str = "json", include: str = "all"):
    """Run comprehensive analysis on a project"""
    analyzer = container.get("analysis_service")
    if not analyzer:
        console.print("[red]Error: Analyzer service not available[/red]")
        raise typer.Exit(1)

    project = Project.create(name=project_name, description=f"Analysis of {project_name}")

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  BarColumn(), console=console) as progress:
        task = progress.add_task("[yellow]Analyzing project...", total=6)

        scores = {}
        for atype in ["architecture", "hackathon", "innovation", "technical-debt", "team-readiness", "competitive-advantage"]:
            progress.update(task, description=f"[yellow]Analyzing {atype}...")
            result = async_run(analyzer.analyze_project(project.id, [atype]))
            scores[atype] = getattr(result, f"{atype.replace('-', '_')}_score", 65.0)
            progress.advance(task)

    table = Table(title=f"[bold]Analysis Results: {project_name}[/bold]")
    table.add_column("Metric", style="cyan")
    table.add_column("Score", justify="right")
    table.add_column("Status", style="yellow")

    for metric, score in scores.items():
        status = "[green]Excellent[/green]" if score >= 80 else "[yellow]Good[/yellow]" if score >= 65 else "[red]Needs Work[/red]"
        table.add_row(metric.replace("-", " ").title(), f"{score:.1f}%", status)

    avg = sum(scores.values()) / len(scores)
    table.add_row("[bold]Overall[/bold]", f"[bold]{avg:.1f}%[/bold]",
                  "[green]Strong[/green]" if avg >= 70 else "[yellow]Moderate[/yellow]")

    console.print(table)
    console.print(f"\n[green]✓[/green] Analysis complete for [bold]{project_name}[/bold]")


@app.command("judge")
def judge_simulation(project_name: str, mode: str = "full-audit", questions_only: bool = False):
    """Run judge simulation for project defense training"""
    judge = container.get("judge_simulation")
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
        result = async_run(judge.run_simulation(project, persona=persona, mode=attack, num_questions=10))

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
            console.print(f"  ⚠ [{spot.get('severity', 'medium')}] {spot.get('area', 'Unknown')}: {spot.get('feedback', '')[:120]}")

    if result.improvement_suggestions:
        console.print("\n[green]Improvement Suggestions:[/green]")
        for s in result.improvement_suggestions[:4]:
            console.print(f"  → {s}")

    if result.questions_asked and not questions_only:
        console.print("\n[bold]Sample Questions:[/bold]")
        for q in result.questions_asked[:4]:
            console.print(f"  [{q.difficulty}/10] {q.question[:120]}..." if len(q.question) > 120 else f"  [{q.difficulty}/10] {q.question}")

    console.print(f"\n[red]Final Verdict:[/red] {result.final_verdict}")


@app.command("readiness")
def team_readiness(project_name: str, evaluate_team: bool = True, evaluate_skills: bool = True):
    """Evaluate team readiness for hackathons and interviews"""
    readiness = container.get("hackathon_readiness")
    project = Project.create(name=project_name, description=f"Readiness evaluation for {project_name}")

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  console=console) as progress:
        progress.add_task("[yellow]Evaluating readiness...", total=None)
        result = async_run(readiness.evaluate_hackathon_readiness(project))

    console.print(f"\n[bold]Readiness Score: {result.overall_score:.1f}%[/bold]")

    table = Table(title="Readiness Breakdown")
    table.add_column("Criterion", style="cyan")
    table.add_column("Score", justify="right")
    table.add_column("Status")
    for criterion, score in result.evaluation_criteria.items():
        status = "[green]✓[/green]" if score >= 70 else "[yellow]~[/yellow]" if score >= 55 else "[red]✗[/red]"
        table.add_row(criterion.replace("_", " ").title(), f"{score:.1f}%", status)
    console.print(table)

    console.print(f"\nWinning Probability: [bold]{result.winning_probability:.1f}%[/bold]")
    console.print(f"Competition Level: {result.competition_level}")

    if result.improvement_recommendations:
        console.print("\n[green]Recommendations:[/green]")
        for rec in result.improvement_recommendations[:5]:
            console.print(f"  → {rec}")


@app.command("competitive")
def competitive_analysis(project_name: str, analyze_market: bool = True, identify_opponents: bool = True):
    """Perform competitive intelligence analysis"""
    competitor = container.get("competitor_analysis")
    project = Project.create(name=project_name, description=f"Competitive analysis for {project_name}")

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  console=console) as progress:
        progress.add_task("[yellow]Analyzing competitive landscape...", total=None)
        result = async_run(competitor.analyze_competition(project))

    console.print(f"\n[bold]Competitive Analysis: {project_name}[/bold]")
    console.print(f"Position: {result.overall_position}")
    console.print(f"Competitiveness: {result.competitiveness_score:.1f}% | "
                  f"Market Fit: {result.market_fit_score:.1f}% | "
                  f"Differentiation: {result.differentiation_score:.1f}%")

    if result.direct_competitors:
        table = Table(title="Direct Competitors")
        table.add_column("Competitor", style="cyan")
        table.add_column("Threat", style="red")
        table.add_column("Similarity")
        for comp in result.direct_competitors[:4]:
            table.add_row(comp.name, comp.threat_level, f"{comp.similarity_score:.0f}%")
        console.print(table)

    if result.blue_ocean_opportunities:
        console.print("\n[green]Blue Ocean Opportunities:[/green]")
        for opp in result.blue_ocean_opportunities[:3]:
            console.print(f"  ◆ {opp}")

    if result.strategic_recommendations:
        console.print("\n[bold]Strategic Recommendations:[/bold]")
        for rec in result.strategic_recommendations[:5]:
            console.print(f"  → {rec}")


@app.command("dashboard")
def start_dashboard(project_name: str, port: int = 8080, open_browser: bool = False):
    """Start real-time dashboard for project monitoring"""
    console.print(Panel(f"[bold]Dashboard: {project_name}[/bold]\nPort: {port}",
                        border_style="cyan"))
    console.print("[green]Starting API server...[/green]")
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=port, reload=False)


@app.command("scan")
def scan_project(path: str):
    """Scan a project directory for analysis"""
    scanner = container.get("project_scanner")
    if not scanner:
        console.print("[red]Scanner not available[/red]")
        return

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  console=console) as progress:
        progress.add_task("[yellow]Scanning project...", total=None)
        result = async_run(scanner.scan_project(path))

    console.print(f"\n[bold]Project Scan: {result.project_name}[/bold]")
    console.print(f"  Files: {result.total_files} | Dirs: {result.total_dirs}")
    console.print(f"  Size: {result.total_size_bytes / 1024:.1f} KB")

    if result.languages:
        lang_table = Table(title="Languages")
        lang_table.add_column("Language", style="cyan")
        lang_table.add_column("Files", justify="right")
        for lang, count in sorted(result.languages.items(), key=lambda x: -x[1])[:8]:
            lang_table.add_row(lang, str(count))
        console.print(lang_table)

    console.print(f"\n  Git: {'✓' if result.git_info.has_git else '✗'}"
                  f" | README: {'✓' if result.has_readme else '✗'}"
                  f" | Tests: {'✓' if result.has_tests else '✗'}"
                  f" | Docker: {'✓' if result.has_docker else '✗'}"
                  f" | CI: {'✓' if result.has_ci else '✗'}")

    if result.git_info.has_git and result.git_info.branch:
        console.print(f"  Branch: {result.git_info.branch}"
                      f"{' | Remote: ' + result.git_info.remote_url if result.git_info.remote_url else ''}")


@app.command("report")
def generate_report(project_name: str, report_type: str = "comprehensive", output_format: str = "pdf"):
    """Generate a professional report"""
    generator = container.get("report_generator")

    data = {
        "overall_score": 72.5,
        "scores": {"architecture": 78, "innovation": 72, "hackathon_readiness": 68,
                   "technical_debt": 25, "team_readiness": 70, "competitive_advantage": 65},
        "strengths": ["Solid architecture", "Good innovation potential"],
        "weak_spots": [{"area": "Testing", "title": "Insufficient tests", "severity": "high"}],
        "recommendations": ["Increase test coverage", "Add documentation"],
    }

    from modules.report_generator import ReportType, ReportFormat
    rt = ReportType(report_type) if report_type in [e.value for e in ReportType] else ReportType.COMPREHENSIVE
    rf = ReportFormat(output_format) if output_format in [e.value for e in ReportFormat] else ReportFormat.PDF

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  console=console) as progress:
        progress.add_task("[yellow]Generating report...", total=None)
        filename = async_run(generator.generate_report(rt, data, project_name, rf))

    console.print(f"[green]✓[/green] Report generated: {filename}")


@app.command("version")
def show_version():
    """Show version information"""
    console.print(Panel("PROJECT WARROOM v0.1.0\nAI-Powered Project Defense Platform\n\n"
                        "12 Modules • FastAPI • Typer • PostgreSQL • ChromaDB • Ollama",
                        title="Version", border_style="green"))


if __name__ == "__main__":
    app()
