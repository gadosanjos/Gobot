# 🤖 Gobot — Game-Building Agent

**Gobot** is an AI-powered development assistant that automates repetitive setup and configuration tasks in the Godot game engine.

Game development often involves repetitive, error-prone steps such as scene creation, node configuration, scripting, and wiring components. Gobot streamlines this workflow by interpreting user requests and modifying the project automatically.

---

## 🎯 Problem

Game developers repeatedly perform tasks like:

* Creating scenes
* Attaching scripts
* Configuring physics nodes
* Wiring components

These steps slow development and introduce configuration errors.

Gobot reduces this friction by automating project setup and validation.

---

## 🧠 What Gobot Does

Users can request tasks such as:

* “Add a player with movement controls.”
* “Create an enemy with collision and basic AI.”
* “Add gravity and jump mechanics.”
* “Insert a camera that follows the player.”

Gobot then:

✔ updates the Godot project
✔ generates scripts and scenes
✔ validates the project
✔ reports errors for correction

---

## 🏗️ Agent Pipeline

Gobot follows a modular agent architecture:

### 🔹 Planner (LLM)

* Interprets user requests
* Breaks tasks into actionable steps
* Produces structured plans

### 🔹 Generator (LLM + Templates)

* Produces scripts and scene files
* Uses deterministic templates for engine formats
* Outputs structured patch instructions

### 🔹 Executor (Tools/API)

* Writes files to the Godot project
* Edits scene files
* Runs Godot in headless mode

### 🔹 Validator (Rules + Engine Feedback)

* Verifies project loads successfully
* Detects script and scene errors
* Returns feedback for correction

**Future additions:**

* Project memory/state tracking
* Git integration

---

## 🛠️ Tools & Technologies

* **Godot Engine CLI** — headless execution & validation
* **Filesystem Tools** — project structure manipulation
* **LLM API (Groq)** — planning & code generation

---

## ⚙️ Example Workflow

**User Prompt:**

> Add a controllable player character.

**Pipeline:**

1. Planner creates action steps
2. Generator produces scene & script files
3. Executor writes files & updates project
4. Validator runs Godot and verifies integrity

Result: a working player node added to the scene.

---

## 🚀 Getting Started

### 1️⃣ Clone the repository

```bash
git clone https://github.com/gadosanjos/Gobot.git
cd Gobot
```

### 2️⃣ Install dependencies

Godot as interaction is made via godot headless

### 3️⃣ Run the agent

```bash
python gobot_game_agent/agent.py
```

---

## 📁 Project Structure

```
Gobot/
│
├── gobot_game_agent/
│   ├── agent.py
│   ├── planner.py
│   ├── generator.py
│   ├── validator.py
│   ├── tools.py
│   └── prompts/
│
├── playground/        # Godot project
├── README.md
└── .gitignore
```

---

## 📌 Status

🚧 Active development
🎯 Goal: Fully autonomous Godot scene & gameplay scaffolding
