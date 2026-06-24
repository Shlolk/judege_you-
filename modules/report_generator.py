from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from io import BytesIO
import json

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, ListFlowable, ListItem, Image, KeepTogether
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle
from reportlab.graphics.charts.barcharts import VerticalBarChart

class ReportType(str, Enum):
    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    HACKATHON = "hackathon"
    COMPETITIVE = "competitive"
    ARCHITECTURE = "architecture"
    COMPREHENSIVE = "comprehensive"

class ReportFormat(str, Enum):
    PDF = "pdf"
    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"

class ReportGenerator:
    """Engine for generating professional reports"""
    
    def __init__(self, output_dir: str = "./output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.styles = self._setup_styles()
    
    def _setup_styles(self) -> Dict[str, ParagraphStyle]:
        """Setup ReportLab styles"""
        
        styles = getSampleStyleSheet()
        
        styles.add(ParagraphStyle(
            "WarroomTitle",
            parent=styles["Title"],
            fontSize=24,
            leading=30,
            textColor=HexColor("#1a237e"),
            spaceAfter=20,
        ))
        
        styles.add(ParagraphStyle(
            "WarroomHeading1",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            textColor=HexColor("#283593"),
            spaceBefore=20,
            spaceAfter=10,
        ))
        
        styles.add(ParagraphStyle(
            "WarroomHeading2",
            parent=styles["Heading2"],
            fontSize=14,
            leading=18,
            textColor=HexColor("#3949ab"),
            spaceBefore=15,
            spaceAfter=8,
        ))
        
        styles.add(ParagraphStyle(
            "WarroomBody",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            spaceBefore=4,
            spaceAfter=4,
        ))
        
        styles.add(ParagraphStyle(
            "WarroomScore",
            parent=styles["Normal"],
            fontSize=28,
            leading=34,
            textColor=HexColor("#1b5e20"),
            alignment=TA_CENTER,
            spaceBefore=10,
            spaceAfter=10,
        ))
        
        styles.add(ParagraphStyle(
            "WarroomScoreLabel",
            parent=styles["Normal"],
            fontSize=10,
            leading=12,
            textColor=HexColor("#558b2f"),
            alignment=TA_CENTER,
        ))
        
        return styles
    
    async def generate_report(
        self,
        report_type: ReportType,
        data: Dict[str, Any],
        project_name: str,
        output_format: ReportFormat = ReportFormat.PDF,
        include_charts: bool = True,
    ) -> str:
        """Generate a comprehensive report"""
        
        if output_format == ReportFormat.PDF:
            return await self._generate_pdf(report_type, data, project_name, include_charts)
        elif output_format == ReportFormat.JSON:
            return await self._generate_json(report_type, data, project_name)
        elif output_format == ReportFormat.MARKDOWN:
            return await self._generate_markdown(report_type, data, project_name)
        elif output_format == ReportFormat.HTML:
            return await self._generate_html(report_type, data, project_name)
        
        return await self._generate_pdf(report_type, data, project_name, include_charts)
    
    async def _generate_pdf(
        self,
        report_type: ReportType,
        data: Dict[str, Any],
        project_name: str,
        include_charts: bool,
    ) -> str:
        """Generate PDF report"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"{project_name}_{report_type.value}_{timestamp}.pdf"
        
        doc = SimpleDocTemplate(
            str(filename),
            pagesize=A4,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50,
        )
        
        story = []
        
        # Title page
        story.extend(self._build_title_page(doc, project_name, report_type))
        story.append(PageBreak())
        
        # Table of contents placeholder
        story.extend(self._build_toc())
        
        # Executive summary
        if data.get("overall_score") is not None:
            story.extend(self._build_score_summary(data))
        
        # Analysis details
        story.extend(self._build_analysis_details(data))
        
        # Charts
        if include_charts:
            story.extend(self._build_charts(data))
        
        # Recommendations
        if data.get("recommendations"):
            story.extend(self._build_recommendations(data["recommendations"]))
        
        # Build the document
        doc.build(story)
        
        return str(filename)
    
    def _build_title_page(
        self,
        doc: SimpleDocTemplate,
        project_name: str,
        report_type: ReportType,
    ) -> List:
        """Build the title page"""
        
        story = []
        
        # Add spacing
        story.append(Spacer(1, 2*inch))
        
        # Title
        story.append(Paragraph(
            "PROJECT WARROOM",
            self.styles["WarroomTitle"]
        ))
        story.append(Spacer(1, 0.5*inch))
        
        # Report title
        report_titles = {
            ReportType.EXECUTIVE: "Executive Analysis Report",
            ReportType.TECHNICAL: "Technical Analysis Report",
            ReportType.HACKATHON: "Hackathon Readiness Report",
            ReportType.COMPETITIVE: "Competitive Intelligence Report",
            ReportType.ARCHITECTURE: "Architecture Audit Report",
            ReportType.COMPREHENSIVE: "Comprehensive Analysis Report",
        }
        story.append(Paragraph(
            report_titles.get(report_type, "Analysis Report"),
            self.styles["WarroomHeading1"]
        ))
        story.append(Spacer(1, 0.5*inch))
        
        # Project info
        story.append(Paragraph(f"Project: {project_name}", self.styles["WarroomBody"]))
        story.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", self.styles["WarroomBody"]))
        story.append(Paragraph(f"Type: {report_type.value.title()} Analysis", self.styles["WarroomBody"]))
        story.append(Spacer(1, 0.3*inch))
        
        # Divider
        story.append(Table(
            [[""]],
            colWidths=[6.5*inch],
            style=TableStyle([
                ("LINEBELOW", (0, 0), (-1, -1), 2, HexColor("#1a237e")),
            ])
        ))
        
        return story
    
    def _build_toc(self) -> List:
        """Build table of contents"""
        
        story = []
        story.append(Paragraph("Table of Contents", self.styles["WarroomHeading1"]))
        story.append(Spacer(1, 0.2*inch))
        
        toc_items = [
            "1. Executive Summary",
            "2. Score Overview",
            "3. Detailed Analysis",
            "4. Key Findings",
            "5. Recommendations",
            "6. Appendix",
        ]
        
        for item in toc_items:
            story.append(Paragraph(item, self.styles["WarroomBody"]))
        
        story.append(Spacer(1, 0.5*inch))
        
        return story
    
    def _build_score_summary(self, data: Dict[str, Any]) -> List:
        """Build score summary section"""
        
        story = []
        story.append(Paragraph("Executive Summary", self.styles["WarroomHeading1"]))
        story.append(Spacer(1, 0.2*inch))
        
        # Overall score
        overall = data.get("overall_score", 0)
        
        # Score circle
        drawing = Drawing(200, 200)
        drawing.add(Circle(100, 100, 80))
        drawing.add(String(100, 100, f"{overall:.0f}", fontSize=36, textAnchor="middle"))
        
        score_color = HexColor("#1b5e20") if overall >= 70 else HexColor("#e65100") if overall >= 50 else HexColor("#b71c1c")
        
        story.append(Paragraph(f"Overall Score: {overall:.1f}%", self.styles["WarroomScore"]))
        
        # Score breakdown table
        score_data = [["Metric", "Score"]]
        for key, value in data.get("scores", {}).items():
            if isinstance(value, (int, float)):
                score_data.append([key.replace("_", " ").title(), f"{value:.1f}%"])
        
        if len(score_data) > 1:
            score_table = Table(score_data, colWidths=[3*inch, 1*inch])
            score_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#283593")),
                ("TEXTCOLOR", (0, 0), (-1, 0), white),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("FONTSIZE", (0, 1), (-1, -1), 10),
                ("ALIGN", (1, 0), (1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 1, HexColor("#cccccc")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#f5f5f5")]),
            ]))
            story.append(score_table)
        
        story.append(Spacer(1, 0.3*inch))
        
        return story
    
    def _build_analysis_details(self, data: Dict[str, Any]) -> List:
        """Build detailed analysis section"""
        
        story = []
        story.append(Paragraph("Detailed Analysis", self.styles["WarroomHeading1"]))
        story.append(Spacer(1, 0.2*inch))
        
        # Architecture analysis
        if "architecture_score" in data.get("scores", {}):
            story.append(Paragraph("Architecture Analysis", self.styles["WarroomHeading2"]))
            arch_score = data["scores"]["architecture_score"]
            story.append(Paragraph(
                f"Architecture Score: {arch_score:.1f}%",
                self.styles["WarroomBody"]
            ))
            if data.get("architectural_patterns"):
                patterns = ", ".join(data["architectural_patterns"][:3])
                story.append(Paragraph(f"Patterns: {patterns}", self.styles["WarroomBody"]))
            story.append(Spacer(1, 0.1*inch))
        
        # Weak spots
        weak_spots = data.get("weak_spots", [])
        if weak_spots:
            story.append(Paragraph("Critical Weaknesses", self.styles["WarroomHeading2"]))
            for spot in weak_spots[:5]:
                if isinstance(spot, dict):
                    story.append(Paragraph(
                        f"• {spot.get('title', spot.get('area', 'Issue'))} - Severity: {spot.get('severity', 'medium')}",
                        self.styles["WarroomBody"]
                    ))
                elif isinstance(spot, str):
                    story.append(Paragraph(f"• {spot}", self.styles["WarroomBody"]))
            story.append(Spacer(1, 0.1*inch))
        
        # Strengths
        strengths = data.get("strengths", [])
        if strengths:
            story.append(Paragraph("Key Strengths", self.styles["WarroomHeading2"]))
            for strength in strengths[:5]:
                story.append(Paragraph(f"✓ {strength}", self.styles["WarroomBody"]))
            story.append(Spacer(1, 0.1*inch))
        
        return story
    
    def _build_charts(self, data: Dict[str, Any]) -> List:
        """Build charts section"""
        
        story = []
        story.append(Paragraph("Visual Analysis", self.styles["WarroomHeading1"]))
        story.append(Spacer(1, 0.2*inch))
        
        # Score bar chart
        scores = data.get("scores", {})
        if scores:
            story.append(Paragraph("Score Breakdown", self.styles["WarroomHeading2"]))
            
            # Create bar chart data
            categories = []
            values = []
            for key, value in scores.items():
                if isinstance(value, (int, float)):
                    categories.append(key.replace("_", " ").title()[:15])
                    values.append(value)
            
            if categories and values:
                drawing = Drawing(400, 200)
                bc = VerticalBarChart()
                bc.x = 50
                bc.y = 50
                bc.height = 120
                bc.width = 300
                bc.data = [values]
                bc.categoryAxis.categoryNames = categories
                bc.categoryAxis.labels.fontSize = 8
                bc.valueAxis.valueMin = 0
                bc.valueAxis.valueMax = 100
                bc.valueAxis.valueStep = 20
                bc.bars[0].fillColor = HexColor("#3949ab")
                
                drawing.add(bc)
                story.append(drawing)
                story.append(Spacer(1, 0.3*inch))
        
        return story
    
    def _build_recommendations(self, recommendations: List[str]) -> List:
        """Build recommendations section"""
        
        story = []
        story.append(Paragraph("Recommendations", self.styles["WarroomHeading1"]))
        story.append(Spacer(1, 0.2*inch))
        
        for i, rec in enumerate(recommendations[:10], 1):
            story.append(Paragraph(f"{i}. {rec}", self.styles["WarroomBody"]))
        
        story.append(Spacer(1, 0.5*inch))
        
        # Footer
        story.append(Table(
            [["Generated by PROJECT WARROOM v0.1.0"]],
            colWidths=[6.5*inch],
            style=TableStyle([
                ("LINEABOVE", (0, 0), (-1, -1), 1, HexColor("#cccccc")),
                ("TEXTCOLOR", (0, 0), (-1, -1), HexColor("#666666")),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ])
        ))
        
        return story
    
    async def _generate_json(
        self,
        report_type: ReportType,
        data: Dict[str, Any],
        project_name: str,
    ) -> str:
        """Generate JSON report"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"{project_name}_{report_type.value}_{timestamp}.json"
        
        report = {
            "metadata": {
                "project": project_name,
                "report_type": report_type.value,
                "generated_at": datetime.now().isoformat(),
                "version": "0.1.0",
            },
            "data": data,
        }
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
        
        return str(filename)
    
    async def _generate_markdown(
        self,
        report_type: ReportType,
        data: Dict[str, Any],
        project_name: str,
    ) -> str:
        """Generate Markdown report"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"{project_name}_{report_type.value}_{timestamp}.md"
        
        lines = [
            f"# PROJECT WARROOM - {report_type.value.title()} Report",
            f"",
            f"**Project:** {project_name}",
            f"**Generated:** {datetime.now().strftime('%B %d, %Y %H:%M:%S')}",
            f"**Type:** {report_type.value.title()} Analysis",
            f"",
            f"---",
            f"",
        ]
        
        # Overall score
        if data.get("overall_score") is not None:
            lines.append(f"## Overall Score: {data['overall_score']:.1f}%")
            lines.append("")
        
        # Scores
        if data.get("scores"):
            lines.append("## Score Breakdown")
            lines.append("")
            lines.append("| Metric | Score |")
            lines.append("|--------|-------|")
            for key, value in data["scores"].items():
                if isinstance(value, (int, float)):
                    lines.append(f"| {key.replace('_', ' ').title()} | {value:.1f}% |")
            lines.append("")
        
        # Strengths
        if data.get("strengths"):
            lines.append("## Key Strengths")
            for s in data["strengths"]:
                lines.append(f"- ✓ {s}")
            lines.append("")
        
        # Weaknesses
        if data.get("weak_spots"):
            lines.append("## Critical Weaknesses")
            for spot in data["weak_spots"][:5]:
                if isinstance(spot, dict):
                    lines.append(f"- ⚠ {spot.get('title', spot.get('area', 'Issue'))}")
                elif isinstance(spot, str):
                    lines.append(f"- ⚠ {spot}")
            lines.append("")
        
        # Recommendations
        if data.get("recommendations"):
            lines.append("## Recommendations")
            for i, rec in enumerate(data["recommendations"][:10], 1):
                lines.append(f"{i}. {rec}")
            lines.append("")
        
        content = "\n".join(lines)
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        
        return str(filename)
    
    async def _generate_html(
        self,
        report_type: ReportType,
        data: Dict[str, Any],
        project_name: str,
    ) -> str:
        """Generate HTML report"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"{project_name}_{report_type.value}_{timestamp}.html"
        
        scores = data.get("scores", {})
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PROJECT WARROOM - {report_type.value.title()} Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, sans-serif; margin: 40px; color: #333; }}
        h1 {{ color: #1a237e; border-bottom: 3px solid #1a237e; padding-bottom: 10px; }}
        h2 {{ color: #283593; margin-top: 30px; }}
        .score-card {{ background: #e8eaf6; padding: 20px; border-radius: 8px; text-align: center; }}
        .score-value {{ font-size: 48px; font-weight: bold; color: #1b5e20; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        th {{ background: #283593; color: white; padding: 10px; text-align: left; }}
        td {{ padding: 8px; border-bottom: 1px solid #ddd; }}
        tr:nth-child(even) {{ background: #f5f5f5; }}
        .strong {{ color: #1b5e20; }}
        .weak {{ color: #b71c1c; }}
        .recommendation {{ background: #fff3e0; padding: 10px; margin: 5px 0; border-left: 4px solid #ff9800; }}
    </style>
</head>
<body>
    <h1>PROJECT WARROOM</h1>
    <p><strong>Project:</strong> {project_name}</p>
    <p><strong>Report Type:</strong> {report_type.value.title()} Analysis</p>
    <p><strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y %H:%M:%S')}</p>
    
    <div class="score-card">
        <div class="score-value">{data.get('overall_score', 0):.1f}%</div>
        <div>Overall Score</div>
    </div>
    
    <h2>Score Breakdown</h2>
    <table>
        <tr><th>Metric</th><th>Score</th></tr>
"""
        for key, value in scores.items():
            if isinstance(value, (int, float)):
                html += f"        <tr><td>{key.replace('_', ' ').title()}</td><td>{value:.1f}%</td></tr>\n"
        
        html += "    </table>\n"
        
        if data.get("strengths"):
            html += "    <h2>Key Strengths</h2>\n"
            for s in data["strengths"]:
                html += f'    <p class="strong">✓ {s}</p>\n'
        
        if data.get("weak_spots"):
            html += "    <h2>Critical Weaknesses</h2>\n"
            for spot in data["weak_spots"][:5]:
                title = spot.get("title", spot.get("area", "Issue")) if isinstance(spot, dict) else spot
                html += f'    <p class="weak">⚠ {title}</p>\n'
        
        if data.get("recommendations"):
            html += "    <h2>Recommendations</h2>\n"
            for i, rec in enumerate(data["recommendations"][:10], 1):
                html += f'    <div class="recommendation">{i}. {rec}</div>\n'
        
        html += """
    <hr>
    <p style="color: #666; font-size: 12px;">Generated by PROJECT WARROOM v0.1.0</p>
</body>
</html>
"""
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)
        
        return str(filename)
