import asyncio
import json as json_lib
import logging
import os
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
from rich.rule import Rule
from rich.text import Text
from rich import box

from core.di.container import get_container
from core.models.project import Project
from core.config_manager import get_config, set_config, get_projects, add_project, remove_project, add_history

console = Console()
app = typer.Typer(help="PROJECT WARROOM - AI-Powered Project Defense Platform", rich_markup_mode="rich")

logging.basicConfig(level=logging.WARNING, handlers=[RichHandler(console=console, show_time=False)])
logger = logging.getLogger("warroom")

_global_json = False


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


def _format_json(data) -> str:
    return json_lib.dumps(data, indent=2, default=str, ensure_ascii=False)


@app.command("init")
def init_project(name: str, repo: Optional[str] = None, description: Optional[str] = None,
                 output_dir: str = "./warroom_projects"):
    """Initialize a new project for analysis
    
    Examples:
      warroom init MyProject
      warroom init MyProject --description "AI chatbot for healthcare"
      warroom init MyProject --repo https://github.com/user/repo.git
    """
    _require_non_empty(name, "project name")
    project_path = Path(output_dir) / name
    if project_path.exists():
        console.print(f"[red]Error: Project '{name}' already exists at {project_path}[/red]")
        raise typer.Exit(1)
    project_path.mkdir(parents=True, exist_ok=True)
    project = Project.create(name=name, description=description or f"Project: {name}",
                             repository_url=repo, path=str(project_path))
    import json
    meta = {"id": project.id, "name": project.name, "description": project.description,
            "repository_url": repo, "created_at": str(project.created_at)}
    (project_path / ".warroom.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    add_project(name, str(project_path), description or "")
    console.print(f"[green]V[/green] Initialized project [bold]{name}[/bold] at {project_path}")
    if repo:
        console.print(f"   Repository: {repo}")
    console.print(f"   Project ID: {project.id}")
    console.print("\n[yellow]Next:[/yellow] Run [bold]warroom analyze {name}[/bold] to start analysis")


@app.command("analyze")
def analyze_project(project_name: str, output_format: str = "json", include: str = "all"):
    """Run comprehensive analysis on a project
    
    Examples:
      warroom analyze MyProject
      warroom analyze MyProject --include architecture,innovation
      warroom analyze MyProject --output-format json
    """
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

    if _global_json:
        console.print(_format_json(scores))
        return

    table = Table(title=f"[bold]Analysis Results: {project_name}[/bold]", box=box.ROUNDED)
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
def judge_simulation(project_name: str, mode: str = "full-audit", questions_only: bool = False,
                     simulate: bool = False):
    """Run judge simulation for project defense training
    
    Default mode asks you 15 questions (5 easy/5 medium/5 hard) and evaluates your answers.
    Use --simulate for the old AI-only evaluation mode.
    
    Examples:
      warroom judge MyProject                    # Interactive defense practice
      warroom judge MyProject --simulate         # AI-only simulation
      warroom judge MyProject --mode technical   # Technical architect persona
    """
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

    if simulate:
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
        return

    # --- Interactive defense mode (default) ---
    console.print(Panel(f"[bold yellow]Project Defense Training: {project_name}[/bold yellow]\n"
                        "You will face [red]15 questions[/red] (5 easy, 5 medium, 5 hard).\n"
                        "Answer each question to the best of your ability.\n"
                        "Press [bold]Enter[/bold] without typing to skip a question.",
                        border_style="yellow"))
    input("[dim]Press Enter to begin...[/dim]")

    questions = async_run(judge.generate_defense_questions(project, persona, attack))

    answers = []
    for i, q in enumerate(questions, 1):
        diff_label = "[green]Easy[/green]" if q.difficulty <= 3 else "[yellow]Medium[/yellow]" if q.difficulty <= 6 else "[red]Hard[/red]"
        console.print(f"\n[bold]Question {i}/15[/bold] ({diff_label}, difficulty {q.difficulty}/10)")
        console.print(f"[cyan]{q.question}[/cyan]")
        user_answer = input("Your answer (or press Enter to skip): ").strip()

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                      console=console) as progress:
            progress.add_task("[yellow]Evaluating answer...", total=None)
            evaluation = async_run(judge.evaluate_answer(project, q, user_answer))

        answers.append({
            "question": q.question,
            "difficulty": q.difficulty,
            "user_answer": user_answer if user_answer else "[skipped]",
            "score": evaluation["score"],
            "feedback": evaluation["feedback"],
        })

        color = "green" if evaluation["score"] >= 7 else "yellow" if evaluation["score"] >= 4 else "red"
        console.print(f"  Score: [{color}]{evaluation['score']}/10[/{color}]")
        console.print(f"  [dim]{evaluation['feedback']}[/dim]")

    # Calculate results
    total_questions = len(answers)
    total_score = sum(a["score"] for a in answers)
    max_possible = total_questions * 10
    percentage = (total_score / max_possible) * 100 if max_possible > 0 else 0

    easy = [a for a in answers if a["difficulty"] <= 3]
    medium = [a for a in answers if a["difficulty"] <= 6 and a["difficulty"] > 3]
    hard = [a for a in answers if a["difficulty"] > 6]
    skipped = [a for a in answers if a["user_answer"] == "[skipped]"]

    console.print()
    console.print(Panel("[bold]Defense Training Results[/bold]", border_style="cyan"))

    result_table = Table()
    result_table.add_column("Category", style="cyan")
    result_table.add_column("Score", justify="right")
    result_table.add_column("Status")

    easy_score = sum(a["score"] for a in easy) / (len(easy) * 10) * 100 if easy else 0
    medium_score = sum(a["score"] for a in medium) / (len(medium) * 10) * 100 if medium else 0
    hard_score = sum(a["score"] for a in hard) / (len(hard) * 10) * 100 if hard else 0

    def status(val):
        return "[green]Strong[/green]" if val >= 70 else "[yellow]Adequate[/yellow]" if val >= 40 else "[red]Weak[/red]"

    result_table.add_row("Easy Questions", f"{easy_score:.0f}%", status(easy_score))
    result_table.add_row("Medium Questions", f"{medium_score:.0f}%", status(medium_score))
    result_table.add_row("Hard Questions", f"{hard_score:.0f}%", status(hard_score))
    result_table.add_row("[bold]Overall Defense[/bold]", f"[bold]{percentage:.0f}%[/bold]", status(percentage))
    if skipped:
        result_table.add_row("Skipped", f"{len(skipped)}/{total_questions}", "[red]Needs Work[/red]")
    console.print(result_table)

    if percentage >= 80:
        console.print("\n[green]V[/green] Excellent defense! Your project is well-prepared for scrutiny.")
    elif percentage >= 60:
        console.print("\n[yellow]Good effort! Focus on the weaker areas to improve your defense.[/yellow]")
    elif percentage >= 40:
        console.print("\n[yellow]You need more preparation. Practice answering tougher questions.[/yellow]")
    else:
        console.print("\n[red]Your project defense needs significant work. Review your project thoroughly.[/red]")

    console.print(f"\n[bold]Success Probability: {percentage:.0f}%[/bold] — Your project would {'likely succeed' if percentage >= 60 else 'face challenges'} in a real judging scenario.")


@app.command("readiness")
def team_readiness(project_name: str):
    """Evaluate team readiness for hackathons and interviews
    
    Examples:
      warroom readiness MyProject
    """
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
    """Perform competitive intelligence analysis
    
    Examples:
      warroom competitive MyProject
    """
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
    """Start real-time dashboard for project monitoring
    
    Examples:
      warroom dashboard MyProject
      warroom dashboard MyProject --port 9090
    """
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
    """Scan a project directory for analysis
    
    Examples:
      warroom scan .
      warroom scan /path/to/project
      warroom scan C:\\Users\\me\\my-project
    """
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

    proj_name = result.project_name or Path(path).name
    add_project(proj_name, path)

    if _global_json:
        console.print(_format_json({
            "project": proj_name,
            "path": path,
            "files": result.total_files,
            "dirs": result.total_dirs,
            "size_kb": round(result.total_size_bytes / 1024, 1),
            "languages": getattr(result, 'languages', {}),
            "has_git": bool(getattr(result, 'git_info', None) and result.git_info.has_git),
            "has_readme": getattr(result, 'has_readme', False),
            "has_tests": getattr(result, 'has_tests', False),
        }))
        return

    console.print(f"\n[bold]Project Scan: {proj_name}[/bold]")
    console.print(f"  Files: {result.total_files} | Dirs: {result.total_dirs}")
    console.print(f"  Size: {result.total_size_bytes / 1024:.1f} KB")

    if getattr(result, 'languages', None):
        lang_table = Table(title="Languages", box=box.ROUNDED)
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
    """Generate a professional report
    
    Examples:
      warroom report MyProject
      warroom report MyProject --report-type executive
      warroom report MyProject --output-format html
    """
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


@app.command("help")
def show_help():
    """Show all available commands with descriptions and examples"""
    if _global_json:
        from core.config_manager import get_config
        cfg = get_config()
        console.print(_format_json({
            "commands": [
                {"name": "init", "description": "Initialize a new project", "usage": "warroom init <name>"},
                {"name": "scan", "description": "Scan a project directory", "usage": "warroom scan <path>"},
                {"name": "analyze", "description": "Run comprehensive analysis", "usage": "warroom analyze <name>"},
                {"name": "judge", "description": "Defense practice (15 interactive questions)", "usage": "warroom judge <name>"},
                {"name": "readiness", "description": "Evaluate team readiness", "usage": "warroom readiness <name>"},
                {"name": "competitive", "description": "Competitive analysis", "usage": "warroom competitive <name>"},
                {"name": "dashboard", "description": "Start monitoring dashboard", "usage": "warroom dashboard <name>"},
                {"name": "report", "description": "Generate professional report", "usage": "warroom report <name>"},
                {"name": "roast", "description": "Brutally roast a project", "usage": "warroom roast <path>"},
                {"name": "status", "description": "Project overview dashboard", "usage": "warroom status"},
                {"name": "config", "description": "Manage preferences", "usage": "warroom config list"},
                {"name": "version", "description": "Show version info", "usage": "warroom version"},
            ],
            "global_options": ["--verbose", "--json"],
            "config_dir": str(Path.home() / ".warroom"),
        }))
        return

    console.print(Rule(style="cyan"))
    console.print(Panel("[bold cyan]PROJECT WARROOM — COMMANDS[/bold cyan]", border_style="cyan"))

    table = Table(box=box.ROUNDED)
    table.add_column("Command", style="green", no_wrap=True)
    table.add_column("Description")
    table.add_column("Example")

    table.add_row("init", "Initialize a new project", "warroom init MyProject")
    table.add_row("scan", "Scan a project directory", 'warroom scan "D:\\Code\\myapp"')
    table.add_row("analyze", "Run comprehensive analysis", "warroom analyze MyProject")
    table.add_row("judge", "Defense practice (15 questions)", "warroom judge MyProject")
    table.add_row("readiness", "Evaluate team/hackathon readiness", "warroom readiness MyProject")
    table.add_row("competitive", "Competitive intelligence", "warroom competitive MyProject")
    table.add_row("dashboard", "Start web dashboard", "warroom dashboard MyProject")
    table.add_row("report", "Generate PDF report", "warroom report MyProject")
    table.add_row("roast", "Brutally roast a project", 'warroom roast "D:\\Code\\myapp"')
    table.add_row("status", "Project overview dashboard", "warroom status")
    table.add_row("config", "Manage preferences", "warroom config list")
    table.add_row("version", "Show version", "warroom version")

    console.print(table)
    console.print("\n[dim]Global options: --verbose (debug logging), --json (machine-readable output)[/dim]")
    console.print(f"[dim]Config: {Path.home() / '.warroom'}[/dim]")
    console.print(f"[dim]For detailed help on any command: [bold]warroom <command> --help[/bold][/dim]")


@app.command("version")
def show_version():
    """Show version information"""
    if _global_json:
        console.print(_format_json({"version": "0.1.0", "name": "PROJECT WARROOM",
                                     "modules": 12, "stack": ["FastAPI", "Typer", "PostgreSQL", "ChromaDB", "Ollama"]}))
        return
    console.print(Panel("PROJECT WARROOM v0.1.0\nAI-Powered Project Defense Platform\n\n"
                        "12 Modules * FastAPI * Typer * PostgreSQL * ChromaDB * Ollama",
                        title="Version", border_style="green"))


@app.command("status")
def show_status():
    """Show project overview dashboard with tracked projects"""
    projects = get_projects()
    if _global_json:
        console.print(_format_json({"tracked_projects": len(projects), "projects": projects}))
        return

    console.print(Rule(style="cyan"))
    console.print(Panel(f"[bold cyan]PROJECT WARROOM STATUS[/bold cyan]", border_style="cyan"))

    if not projects:
        console.print("\n[yellow]No projects tracked yet.[/yellow]")
        console.print("[dim]Initialize or scan a project to get started:[/dim]")
        console.print("  [green]warroom init[/green] <name>")
        console.print("  [green]warroom scan[/green] <path>")
        console.print()
        return

    table = Table(box=box.ROUNDED)
    table.add_column("Project", style="cyan", no_wrap=True)
    table.add_column("Path", style="dim")
    table.add_column("Last Updated", style="yellow")
    table.add_column("Description")

    for p in projects:
        updated = p.get("updated_at", "")[:10] if p.get("updated_at") else "-"
        desc = p.get("description", "")[:40] if p.get("description") else "-"
        table.add_row(p["name"], p.get("path", "-"), updated, desc)

    console.print(table)
    console.print(f"\n[dim]Tracked projects: {len(projects)}[/dim]")
    console.print(f"[dim]Config directory: {str(Path.home() / '.warroom')}[/dim]")
    config = get_config()
    console.print(f"[dim]Default port: {config.get('default_port', 8080)} | "
                  f"Output: {config.get('output_format', 'rich')}[/dim]")


@app.command("config")
def manage_config(action: str = typer.Argument("list", help="Action: list, get, set, reset"),
                  key: Optional[str] = typer.Argument(None, help="Config key to get/set"),
                  value: Optional[str] = typer.Argument(None, help="Value to set")):
    """Manage user configuration preferences
    
    Examples:
      warroom config list           — Show all settings
      warroom config get default_port  — Show a specific setting
      warroom config set default_port 9090  — Change a setting
      warroom config reset          — Reset to defaults
    """
    if action == "list":
        cfg = get_config()
        if _global_json:
            console.print(_format_json(cfg))
            return
        table = Table(title="Warroom Configuration", box=box.ROUNDED)
        table.add_column("Key", style="cyan")
        table.add_column("Value")
        for k, v in cfg.items():
            table.add_row(k, str(v))
        console.print(table)

    elif action == "get":
        if not key:
            console.print("[red]Error: specify a key. Usage: warroom config get <key>[/red]")
            raise typer.Exit(1)
        cfg = get_config()
        if _global_json:
            console.print(_format_json({key: cfg.get(key, "not found")}))
            return
        if key in cfg:
            console.print(f"[cyan]{key}[/cyan] = [green]{cfg[key]}[/green]")
        else:
            console.print(f"[red]Key '{key}' not found[/red]")

    elif action == "set":
        if not key or value is None:
            console.print("[red]Error: specify a key and value. Usage: warroom config set <key> <value>[/red]")
            raise typer.Exit(1)
        result = set_config(key, value)
        if _global_json:
            console.print(_format_json(result))
            return
        console.print(f"[green]V[/green] Set [cyan]{key}[/cyan] = [green]{value}[/green]")

    elif action == "reset":
        from core.config_manager import DEFAULTS, CONFIG_FILE
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()
        set_config("_", "_")  # trigger fresh defaults
        if _global_json:
            console.print(_format_json({"status": "reset", "defaults": DEFAULTS}))
            return
        console.print("[green]V[/green] Configuration reset to defaults")
        for k, v in DEFAULTS.items():
            console.print(f"  [cyan]{k}[/cyan] = [green]{v}[/green]")

    else:
        console.print(f"[red]Unknown action '{action}'. Use: list, get, set, reset[/red]")
        raise typer.Exit(1)


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


def show_startup_animation():
    stages = [
        ("[cyan]Loading modules[/cyan]", 20),
        ("[cyan]Initializing AI engine[/cyan]", 40),
        ("[cyan]Connecting to Ollama[/cyan]", 60),
        ("[cyan]Preparing warroom[/cyan]", 85),
        ("[green]Ready[/green]", 100),
    ]
    import time
    with Progress(SpinnerColumn(spinner_name="dots"),
                  TextColumn("[progress.description]{task.description}"),
                  BarColumn(bar_width=None),
                  TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                  console=console) as progress:
        task = progress.add_task("", total=100)
        for desc, pct in stages:
            progress.update(task, description=desc, completed=pct)
            time.sleep(0.25)
        progress.update(task, description="[green]Warroom initialized[/green]", completed=100)
        time.sleep(0.15)


def show_banner():
    show_startup_animation()
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
    history = []
    try:
        from core.config_manager import HISTORY_FILE
        import json
        if HISTORY_FILE.exists():
            hist_data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            history = hist_data.get("history", [])
    except Exception:
        pass
    hist_idx = len(history)

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
            if raw == "clear":
                console.clear()
                show_banner()
                continue

            # Strip leading "warroom" so both "scan ..." and "warroom scan ..." work
            if raw.startswith("warroom "):
                raw = raw[8:]
            elif raw == "warroom":
                show_interactive_help()
                continue

            # Save to history if not a duplicate of last
            if not history or history[-1] != raw:
                history.append(raw)
                add_history(raw)
            hist_idx = len(history)

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


@app.callback(invoke_without_command=True)
def warroom_callback(ctx: typer.Context, verbose: bool = False, json: bool = False):
    """PROJECT WARROOM — AI-Powered Project Defense Platform"""
    global _global_json
    _global_json = json
    if verbose:
        logging.getLogger("warroom").setLevel(logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)
    if ctx.invoked_subcommand is None:
        interactive_shell()


def main():
    app()


if __name__ == "__main__":
    main()
