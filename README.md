# PROJECT WARROOM 🛡️

**AI-Powered Project Defense Platform**

> *"GitHub Copilot + SIH Judge + Technical Interviewer + Architecture Reviewer + Project Consultant"*

**Not a chatbot. Not a ChatGPT wrapper. A complete project defense operating system.**

---

## What Makes This Different?

While ChatGPT answers questions, PROJECT WARROOM **attacks your project** — discovering weaknesses, simulating judges, stress-testing architecture, and training your team to defend their work. Every feature answers the question: *"Why can't ChatGPT do this?"*

| Feature | ChatGPT | PROJECT WARROOM |
|---------|---------|-----------------|
| Code analysis | Generic | Deep architecture audit with risk scoring |
| Project review | Text-only | Multi-dimensional (code + docs + team + market) |
| Interview prep | General advice | Judge persona simulation with cross-examination |
| Hackathon readiness | No | Winning probability + readiness engine |
| Competitive analysis | Basic research | Real competitor intelligence + blue ocean detection |

---

## Features

### 12 Core Modules

| Module | What It Does |
|--------|-------------|
| **Project Scanner** | Analyzes project structure, languages, dependencies, git history |
| **Architecture Auditor** | Scores architecture quality, detects anti-patterns, calculates risk |
| **Hackathon Readiness Engine** | Evaluates project for hackathons, predicts winning probability |
| **Judge Simulation Engine** | 7 judge personas (SIH, VC, Professor, etc.) with attack modes |
| **Interview Simulation Engine** | Technical + behavioral + system design interview training |
| **Weakness Detection Engine** | Scans for security, performance, testing, and design weaknesses |
| **PPT Analyzer** | Evaluates presentations for structure, content, and visual quality |
| **Documentation Auditor** | Checks README, API docs, and technical documentation quality |
| **Competitor Analysis Engine** | Identifies competitors, market gaps, and blue ocean opportunities |
| **Report Generator** | Generates PDF, JSON, HTML, and Markdown reports with charts |
| **Knowledge Base Engine** | Learns from past analyses, stores patterns and best practices |
| **AI Reasoning Engine** | Chain-of-thought, tree-of-thought, and hypothesis testing reasoning |

### Unique Capabilities

- ❌ **Architecture Battle Mode** — Pit two architectures against each other
- ❌ **Judge Attack Simulation** — Get cross-examined like a real hackathon
- ❌ **Innovation Detection** — Identifies if you're building a "ChatGPT wrapper"
- ❌ **Selection Probability Predictor** — Calculates your chance of winning
- ❌ **Technical Debt Analyzer** — Quantifies debt with actionable remediation
- ❌ **Team Readiness Score** — Evaluates skills, roles, and gaps
- ❌ **Cross Examination Mode** — Legal-style stress testing of your project
- ❌ **Project Defense Training** — Practice mode for judge Q&A

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     CLI (Typer + Rich)                   │
├─────────────────────────────────────────────────────────┤
│                    FastAPI Backend                       │
├─────────────────────────────────────────────────────────┤
│   Core Services  │  Analysis Modules  │  AI Layer        │
│   - DI Container │  - 12 Modules      │  - Ollama/Gemma  │
│   - Repository   │  - Pluggable       │  - Embeddings    │
│   - DDD Models   │  - Extensible      │  - ChromaDB      │
├─────────────────────────────────────────────────────────┤
│   Parsers │ Database │ Reports │ Knowledge Base         │
├─────────────────────────────────────────────────────────┤
│   PostgreSQL │ Redis │ ChromaDB │ Ollama │ Docker        │
└─────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3.12 |
| **CLI** | Typer + Rich |
| **Backend** | FastAPI + Uvicorn |
| **Database** | PostgreSQL 15 + Redis 7 |
| **Vector DB** | ChromaDB |
| **AI** | Ollama (Gemma 3) + Sentence Transformers |
| **Parsing** | PyPDF, python-pptx, Tree-sitter |
| **Reporting** | ReportLab |
| **Infrastructure** | Docker Compose |

---

## Quick Start

### Prerequisites

- Python 3.12+
- Docker & Docker Compose (for services)
- Ollama (for AI features)

### Installation

```bash
# Clone the repository
git clone https://github.com/Shlolk/judege_you-.git
cd project-warroom

# Install dependencies
pip install -r requirements.txt

# Start infrastructure services
docker-compose up -d postgres redis chromadb

# Pull AI model
ollama pull gemma3:latest
```

### CLI Usage

```bash
# Initialize a project
python -m cli.commands init my-project --repo https://github.com/user/repo

# Run comprehensive analysis
python -m cli.commands analyze my-project --format json

# Run judge simulation
python -m cli.commands judge my-project --mode full-audit

# Check team readiness
python -m cli.commands readiness my-project --evaluate-team

# Start dashboard
python -m cli.commands dashboard my-project --port 8080
```

### API Usage

```bash
# Start the API server
uvicorn api.main:app --host 0.0.0.0 --port 8080

# Analyze a project
curl -X POST http://localhost:8080/api/v1/analysis/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "my-project",
    "project_description": "My awesome project",
    "analysis_types": ["architecture", "hackathon", "weakness"]
  }'

# Run judge simulation
curl -X POST http://localhost:8080/api/v1/simulation/judge \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "my-project",
    "project_description": "My awesome project",
    "persona": "sih_judge",
    "mode": "aggressive"
  }'
```

### Docker Deployment

```bash
# Full stack deployment
docker-compose up -d

# Access the API at http://localhost:8080
# API docs at http://localhost:8080/docs
```

---

## Project Structure

```
├── api/                    # FastAPI backend
│   ├── main.py            # Application entry point
│   └── routes/            # API route handlers
├── cli/                   # Command-line interface
│   └── commands.py        # Typer CLI commands
├── core/                  # Business logic
│   ├── models/            # Domain models
│   ├── services/          # Service layer
│   └── di/               # Dependency injection
├── modules/               # Analysis modules (12)
│   ├── project_scanner.py
│   ├── architecture_auditor.py
│   ├── hackathon_readiness_engine.py
│   ├── judge_simulation_engine.py
│   ├── interview_simulation_engine.py
│   ├── weakness_detection_engine.py
│   ├── competitor_analysis_engine.py
│   ├── report_generator.py
│   ├── knowledge_base_engine.py
│   └── ai_reasoning_engine.py
├── ai/                    # AI integration layer
│   ├── models/            # Ollama client
│   └── embeddings.py      # Vector embeddings
├── parsers/               # File parsers
│   ├── code_parser.py     # Tree-sitter code analysis
│   ├── document_parser.py # Markdown/PDF/text parsing
│   └── ppt_parser.py      # PowerPoint analysis
├── database/              # Data layer
│   ├── models/            # SQLAlchemy models
│   ├── repositories/      # Repository implementations
│   ├── migrations/        # Alembic migrations
│   └── config.py          # Database configuration
├── reports/               # Report generation
├── tests/                 # Test suite
├── config/                # Configuration
├── Dockerfile             # Container build
├── docker-compose.yml     # Service orchestration
└── requirements.txt       # Python dependencies
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/projects/` | Create project |
| POST | `/api/v1/projects/scan` | Scan project directory |
| POST | `/api/v1/projects/clone` | Clone git repository |
| POST | `/api/v1/analysis/analyze` | Run project analysis |
| GET | `/api/v1/analysis/{id}/scores` | Get analysis scores |
| POST | `/api/v1/simulation/judge` | Run judge simulation |
| POST | `/api/v1/simulation/interview` | Run interview simulation |
| POST | `/api/v1/simulation/cross-examination` | Run cross-examination |
| POST | `/api/v1/reports/generate` | Generate report |
| POST | `/api/v1/competitive/analyze` | Competitive analysis |

---

## Development Roadmap

### v0.1.0 ✅ Current
- Core architecture and module structure
- 12 analysis modules with AI integration
- RESTful API with FastAPI
- CLI with Typer + Rich
- Database migrations and schema
- Docker deployment

### v0.2.0 🔜 Next
- Architecture Battle Mode (A/B comparison)
- Real-time collaborative dashboards
- WebSocket-based live simulation
- Advanced LLM integration (Gemma 3 fine-tuning)
- CI/CD pipeline with GitHub Actions
- Comprehensive test suite (80%+ coverage)

### v1.0.0 🎯 Target
- Multi-project comparison and benchmarking
- Team collaboration features
- Plugin system for custom modules
- Cloud deployment (AWS/GCP/Azure)
- Enterprise SSO and RBAC
- Marketplace for judge personas

---

## Why PROJECT WARROOM?

**For Students:** Prepare for hackathon judging with realistic judge simulation across 7 personas. Get scored, find weaknesses, improve before the real event.

**For Developers:** Audit your architecture, detect technical debt, and prepare for technical interviews with system design questions tailored to your project.

**For Startup Founders:** Analyze competitive landscape, identify blue ocean opportunities, and prepare for investor pitches with VC judge persona.

**For Hackathon Teams:** Evaluate readiness, predict winning probability, and train for cross-examination with aggressive judge mode.

**For Freelancers:** Document your project quality with professional reports, impress clients with architecture scores, and prepare for client defense.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built with ❤️ for every student, developer, and founder who needs to defend their work.*
