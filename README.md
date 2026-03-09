# 🤖 Gobot — Godot Game-Building Agent

**Gobot** is an AI-powered development assistant for the **Godot game engine**.

It helps automate repetitive development tasks by interpreting user goals, inspecting the current project, generating code patches, applying them, and validating the result through Godot’s headless runtime.

Rather than acting as a simple code generator, Gobot is evolving into a **tool-using agent** that can reason step-by-step about project changes.

---

## 🎯 Problem

Game development often involves repetitive and error-prone setup work such as:

- inspecting project structure
- modifying scripts
- wiring gameplay logic
- validating whether changes actually run in-engine

These steps slow iteration and can easily introduce engine-specific errors.

Gobot reduces this friction by helping automate script generation, project inspection, patch application, and validation.

---

## 🧠 What Gobot Can Do Now

Gobot currently supports a **script-first development workflow**.

Users can request tasks such as:

- “Make the player move in top-down style.”
- “Add health and damage handling to the player.”
- “Inspect the current player script.”
- “Modify movement to only allow vertical input.”

Gobot can then:

✔ inspect the current project structure  
✔ read relevant files before editing  
✔ create a structured plan  
✔ generate script patches  
✔ apply patches to the Godot project  
✔ run Godot in headless mode  
✔ inspect runtime/script errors  
✔ continue iterating step-by-step

---

## 🏗️ Current Architectures

Gobot currently contains **two runtimes**:

### 1. `agent.py` — Original Linear Pipeline
This is the earlier pipeline kept for comparison and debugging.

Flow:

```text
User Goal
   ↓
Planner
   ↓
Generator
   ↓
Executor
   ↓
Validator
```

This version is simpler and useful for testing the earlier non-agent workflow.

---

### 2. `react_agent.py` — ReAct Agent Runtime
This is the newer runtime that introduces a **reasoning loop**.

Flow:

```text
User Goal
   ↓
Thought
   ↓
Action
   ↓
Observation
   ↓
Thought
   ↓
Action
   ↓
Observation
   ↓
... repeat until done
```

This allows Gobot to:

- inspect files before editing
- reason about what tool to use next
- react to Godot runtime errors
- iterate instead of following one fixed pipeline

---

## 🔁 ReAct Agent Loop

The current ReAct-style runtime uses tool calls such as:

- `list_files`
- `read_file`
- `plan`
- `generate_patch`
- `apply_patch`
- `run_godot`
- `validate`

Typical flow:

```text
Inspect project
   ↓
Read relevant file
   ↓
Create/update plan
   ↓
Generate patch
   ↓
Apply patch
   ↓
Run Godot headless
   ↓
Validate result
   ↓
If needed, inspect error and iterate
```

---

## 🧩 Core Components

### 🔹 Planner
- Interprets the user request
- Produces structured task steps
- Provides a high-level development plan

### 🔹 Generator
- Produces Godot-compatible script patches
- Uses prompt templates and retrieved grounding docs
- Outputs structured JSON patch data

### 🔹 Executor / Tools
- Writes files into the Godot project
- Reads files for inspection
- Lists project files
- Runs Godot in headless mode

### 🔹 Validator
- Checks runtime result from Godot
- Detects script/scene parse errors
- Returns feedback for correction

### 🔹 Retriever
- Supplies Godot-specific grounding knowledge
- Helps the generator stay closer to valid engine usage

---

## 🛠️ Tools & Technologies

- **Godot Engine CLI** — headless execution & validation
- **Python** — agent runtime and tooling
- **Filesystem tools** — patch application and file inspection
- **Groq LLM API** — planning and code generation
- **Prompt templates** — structured planner/generator/agent prompting

---

## 🛡️ Safety & Validation

To reduce bad edits, Gobot includes:

- path safety checks
- duplicate file detection
- restricted project-relative writes
- scene format validation
- runtime validation through Godot headless mode

---

## ⚙️ Example Workflow

### User Prompt
> Make the player move fluidly like in a top-down Diablo-style game, and add basic damage handling.

### Agent Flow
1. Inspect project files
2. Read the current `Player.gd`
3. Plan required changes
4. Generate a patch
5. Apply patch
6. Run Godot headless
7. Inspect errors if needed
8. Iterate

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/gadosanjos/Gobot.git
cd Gobot
```

### 2. Install dependencies

```bash
pip install -r gobot_game_agent/requirements.txt
```

You also need a local Godot executable configured for headless use.

### 3. Run the original pipeline

```bash
python gobot_game_agent/agent.py
```

### 4. Run the ReAct runtime

```bash
python gobot_game_agent/react_agent.py
```

---

## 📁 Project Structure

```text
Gobot/
│
├── gobot_game_agent/
│   ├── agent.py              # original linear pipeline
│   ├── react_agent.py        # ReAct runtime
│   ├── planner.py
│   ├── generator.py
│   ├── retriever.py
│   ├── validator.py
│   ├── tools.py
│   ├── prompts/
│   │   └── prompt_template.py
│   └── knowledge/
│
├── playground/               # Godot project under test
├── README.md
└── .gitignore
```

---

## 📌 Current Status

🚧 Active development

Current focus:
- stabilizing the ReAct runtime
- improving tool-call discipline
- improving generated GDScript quality
- iterating safely through Godot runtime feedback

Planned future work:
- stronger memory/state tracking
- search over project code
- better retry logic
- better planning discipline
- Git-aware workflows
- broader scene automation
