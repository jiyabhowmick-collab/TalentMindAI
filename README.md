<div align="center">

<img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&size=32&pause=1000&color=6C63FF&center=true&vCenter=true&width=600&lines=TalentMind+AI;Workforce+Intelligence+;Career+Readiness" alt="Typing SVG" />

<br/>

<p>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Flask-2.x-000000?style=for-the-badge&logo=flask&logoColor=white"/>
  <img src="https://img.shields.io/badge/TypeScript-55.6%25-3178C6?style=for-the-badge&logo=typescript&logoColor=white"/>
  <img src="https://img.shields.io/badge/JavaScript-10.4%25-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black"/>
  <img src="https://img.shields.io/badge/CSS3-1.4%25-1572B6?style=for-the-badge&logo=css3&logoColor=white"/>
</p>

<p>
  <img src="https://img.shields.io/badge/Microsoft_Agents_League-Reasoning_Agents_Track-0078D4?style=for-the-badge&logo=microsoft&logoColor=white"/>
  <img src="https://img.shields.io/badge/India_Runs_Data_%26_AI_Challenge-Participant-FF6B35?style=for-the-badge"/>
</p>

<br/>

> **An AI-powered workforce intelligence platform** that brings together multi-agent reasoning to help organizations discover top talent, close skill gaps, and build future-ready teams — all in one place.

</div>

---

## 📸 Screenshots

<table>
  <tr>
    <td align="center" width="33%">
      <img src="https://github.com/user-attachments/assets/6cec5295-6121-4ba2-8f84-4c5c89753764" alt="Landing Page" height="420"/>
      <br/><sub><b>🏠 Landing Page</b></sub>
    </td>
    <td align="center" width="33%">
      <img src="https://github.com/user-attachments/assets/dbe6b42d-bff1-44e6-8149-e126f0c8f75d" alt="Login Page" height="420"/>
      <br/><sub><b>🔐 Login / Auth</b></sub>
    </td>
    <td align="center" width="33%">
      <img src="https://github.com/user-attachments/assets/f6ddab48-a7b3-45f3-bda5-1c78037d19d7" alt="Candidate Ranker" height="420"/>
      <br/><sub><b>🤖 Candidate Ranker</b></sub>
    </td>
  </tr>
</table>

---

## 🏗️ System Architecture

> *Architecture diagram coming soon — SVG will be placed here.*

<!-- ARCHITECTURE SVG PLACEHOLDER -->
<!-- Replace the comment below with your SVG file or image tag -->
<!--
<div align="center">
  <img src="./assets/architecture.svg" alt="TalentMind AI Architecture" width="90%"/>
</div>
-->

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Problem Statement](#-problem-statement)
- [Key Features](#-key-features)
- [Multi-Agent Architecture](#-multi-agent-architecture)
- [Tech Stack](#️-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [How It Works](#️-how-it-works)
- [Hackathon Alignment](#-hackathon-alignment)
- [Future Roadmap](#-future-roadmap)
- [Contributors](#-contributors)

---

## 🌟 Overview

**TalentMind AI** is an AI-powered workforce intelligence platform that helps organizations:

- 🎯 **Identify the best candidates** using intelligent ranking beyond keyword matching
- 📚 **Recommend personalized learning paths** tailored to each role and individual
- 📊 **Assess workforce readiness** with data-driven metrics and scoring
- 📈 **Provide workforce analytics** to surface top performers and flag at-risk employees

The platform unifies recruitment intelligence and employee development into a single AI-driven solution — powered by a multi-agent reasoning architecture that thinks, collaborates, and acts.

---

## 🚨 Problem Statement
Recruiters are tasked with finding the perfect fit from massive candidate pools, but traditional keyword filters miss hidden gems — candidates whose true potential and behavioral signals are lost in the noise.

> **The Mission:** Build a robust Proof-of-Concept that intelligently ranks candidates — going beyond keywords to understand semantic fit, interpret complex job descriptions, and integrate behavioral/activity signals to deliver a fast, accurate ranked shortlist.

Traditional recruitment and workforce management struggles with:

|
 Pain Point 
|
 Impact 
|
| --- | --- |
| Keyword-only resume screening 
|
 Misses highly qualified candidates whose potential is buried in the noise 
|
|
 No semantic understanding 
|
 Complex job descriptions are poorly matched against real candidate strengths 
|
|
 Ignored behavioral signals 
|
 Activity patterns and soft signals that reveal true fit go unanalyzed 
|
|
 Manual skill gap analysis 
|
 Slow, error-prone, and unable to scale across large talent pools 
|
|
 Siloed HR & L&D tools 
|
 No unified intelligence layer for end-to-end workforce decisions 
|
|
 Lack of readiness metrics 
|
 Poor succession planning and missed internal mobility opportunities 
|

**TalentMind AI** solves these challenges through coordinated AI agents that reason across recruitment, learning, assessment, and analytics — simultaneously delivering a ranked shortlist that reflects true candidate potential, not just keyword overlap.

---

## ✨ Key Features

### 🤖 Candidate Ranking Agent
- Matches candidates against job descriptions with deep semantic understanding
- Calculates multi-dimensional suitability scores
- Returns a ranked list of top candidates with reasoning

### 📚 Learning Path Agent
- Generates role-based certification and course recommendations
- Creates personalized upskilling plans per employee
- Supports career progression and continuous learning

### 📝 Assessment Agent
- Evaluates candidate and employee readiness scores
- Factors in study hours, performance metrics, and skill profiles
- Provides actionable improvement recommendations

### 📊 Analytics Dashboard
- Real-time workforce readiness overview
- Highlights top performers across departments
- Identifies at-risk employees needing intervention

---

## 🧠 Multi-Agent Architecture

TalentMind AI is built on a **multi-agent orchestration model** where specialized AI agents collaborate through a centralized workflow orchestrator.

```
┌─────────────────────────────────────────────┐
│              Orchestrator Layer              │
│         (Centralized Workflow Engine)        │
└──────┬────────────┬────────────┬─────────────┘
       │            │            │
       ▼            ▼            ▼
┌──────────┐  ┌──────────┐  ┌──────────────┐
│Candidate │  │ Learning │  │  Assessment  │
│ Ranking  │  │   Path   │  │    Agent     │
│  Agent   │  │  Agent   │  │              │
└──────────┘  └──────────┘  └──────────────┘
       │            │            │
       └────────────┴────────────┘
                    │
                    ▼
         ┌─────────────────┐
         │    Memory &     │
         │   Agent Logs    │
         └─────────────────┘
```

### Core Capabilities

| Capability | Description |
|---|---|
| 🔄 Multi-Agent Orchestration | Agents collaborate via a shared orchestrator for complex workflows |
| 🧩 Skill Gap Analysis | Identifies missing competencies across the workforce |
| 🏆 Candidate Discovery | Ranks and discovers talent beyond keyword matching |
| 📖 Learning Intelligence | Personalized learning recommendations per role |
| 🧮 Decision Support | Data-backed recommendations for hiring and development |
| 📊 Workforce Analytics | Live dashboards of readiness and performance metrics |

---

## 🛠️ Tech Stack

<table>
  <tr>
    <th>Layer</th>
    <th>Technology</th>
    <th>Purpose</th>
  </tr>
  <tr>
    <td><b>Frontend</b></td>
    <td>TypeScript, JavaScript, HTML5, CSS3</td>
    <td>Interactive UI, dashboards, forms</td>
  </tr>
  <tr>
    <td><b>Backend</b></td>
    <td>Python, Flask</td>
    <td>API server, agent orchestration</td>
  </tr>
  <tr>
    <td><b>AI Agents</b></td>
    <td>Python (custom agent framework)</td>
    <td>Candidate ranking, learning paths, assessments</td>
  </tr>
  <tr>
    <td><b>Data Storage</b></td>
    <td>JSON Datasets</td>
    <td>Candidate profiles, skill data, reports</td>
  </tr>
  <tr>
    <td><b>Memory Layer</b></td>
    <td>In-memory / JSON persistence</td>
    <td>Agent state and conversation history</td>
  </tr>
  <tr>
    <td><b>Version Control</b></td>
    <td>Git, GitHub</td>
    <td>Source control and collaboration</td>
  </tr>
</table>

---

## 📁 Project Structure

```
TalentMindAI/
│
├── app.py                  # Flask entry point
├── requirements.txt        # Python dependencies
├── README.md
│
├── agents/                 # Specialized AI agents
│   ├── candidate_ranking_agent.py
│   ├── learning_path_agent.py
│   └── assessment_agent.py
│
├── orchestrator/           # Multi-agent workflow orchestrator
│
├── data/                   # JSON datasets (candidates, skills, roles)
│
├── memory/                 # Agent memory and session state
│
├── logs/                   # Agent activity and execution logs
│
├── reports/                # Generated analytics reports
│
├── static/                 # CSS, JS, and frontend assets
│
├── templates/              # HTML Jinja2 templates
│
└── assets/                 # Images and architecture diagrams
```

> **Fork note:** The `Joy-S-07/TalentMindAI` fork extends this with a modern `client/`, `server/`, and `sandbox/` structure built in TypeScript for enhanced frontend capabilities.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- pip
- Node.js (for the TypeScript client layer, if applicable)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Joy-S-07/TalentMindAI.git

# 2. Navigate to the project directory
cd TalentMindAI

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Run the Flask application
python app.py

# 5. Open in your browser
# http://127.0.0.1:5000
```

### For the TypeScript client (if applicable)

```bash
cd client
npm install
npm run dev
```

---

## ⚙️ How It Works

```
User Input (Job Description / Employee Data)
            │
            ▼
    ┌──────────────────┐
    │   Orchestrator   │  ← Routes to the right agents
    └────────┬─────────┘
             │
    ┌────────┴─────────────────┐
    │                          │
    ▼                          ▼
Candidate Ranking Agent   Learning Path Agent
(Score & Rank Talent)     (Build Learning Plans)
    │                          │
    └──────────┬───────────────┘
               │
               ▼
       Assessment Agent
   (Readiness Evaluation)
               │
               ▼
     Analytics Dashboard
  (Reports, Metrics, Alerts)
```

1. **Input** — Recruiters or managers provide a job description, employee profile, or skill requirement.
2. **Orchestration** — The workflow orchestrator routes the task to the appropriate agent(s).
3. **Agent Processing** — Specialized agents independently reason and generate outputs.
4. **Memory** — Agent results and state are stored for continuity across sessions.
5. **Output** — Ranked candidates, learning plans, readiness scores, or dashboard analytics are returned to the user.

---

## 🏆 Hackathon Alignment

### 🔵 Microsoft Agents League
**Track: Reasoning Agents**

TalentMind AI demonstrates multi-step reasoning through specialized AI agents that collaborate via a shared orchestrator. It showcases how coordinated agent interactions, structured decision-making, and workflow orchestration can solve real enterprise HR challenges.

### 🟠 India Runs Data & AI Challenge

The platform enables:
- Intelligent candidate discovery and ranking
- Workforce readiness analysis at scale
- Career development powered by data-driven recommendations

---

## 🔮 Future Roadmap

| Feature | Status |
|---|---|
| 📄 Resume Parsing | 🔜 Planned |
| 🧠 Semantic Candidate Matching (Embeddings) | 🔜 Planned |
| 🎙️ AI Interview Assistant | 🔜 Planned |
| 🤝 Multi-Agent Collaboration (expanded) | 🔜 Planned |
| ☁️ Azure AI Foundry Integration | 🔜 Planned |
| 🤖 Microsoft Copilot Integration | 🔜 Planned |
| 📊 Advanced Workforce Analytics | 🔜 Planned |

---

## 👥 Contributors

<table>
  <tr>
    <td align="center" width="200">
      <a href="https://github.com/jiyabhowmick-collab">
        <img src="https://avatars.githubusercontent.com/jiyabhowmick-collab?v=4&s=100" width="100" height="100" style="border-radius:50%" alt="Jiya Bhowmick"/><br/>
        <sub><b>Jiya Bhowmick</b></sub>
      </a><br/>
      <sub>BCA Student · UI/UX Designer · AI Enthusiast</sub>
    </td>
    <td align="center" width="200">
      <a href="https://github.com/Joy-S-07">
        <img src="https://avatars.githubusercontent.com/Joy-S-07?v=4&s=100" width="100" height="100" style="border-radius:50%" alt="Joy-S-07"/><br/>
        <sub><b>Joy-S-07</b></sub>
      </a><br/>
      <sub>Contributor · TypeScript Frontend</sub>
    </td>
    <td align="center" width="200">
      <a href="https://github.com/SnehaBanik">
        <img src="https://avatars.githubusercontent.com/SnehaBanik?v=4&s=100" width="100" height="100" style="border-radius:50%" alt="Sneha Banik"/><br/>
        <sub><b>Sneha Banik</b></sub>
      </a><br/>
      <sub>Contributor</sub>
    </td>
  </tr>
</table>

---

<div align="center">

**⭐ If you find this project valuable, consider starring the repository!**

<br/>

Made with ❤️ for the Microsoft Agents League & India Runs Data & AI Challenge

</div>