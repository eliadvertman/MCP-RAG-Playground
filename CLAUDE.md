# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python project called "mcp_rag_playground" set up as an IntelliJ IDEA project with a Python 3.9 virtual environment.

## Project Structure

- `venv/` - Python 3.9 virtual environment (activated via `venv/Scripts/activate` on Windows or `source venv/bin/activate` on Unix)
- `mcp_rag_playground.iml` - IntelliJ IDEA module configuration file

## Development Environment

- **Python Version**: 3.9.13
- **Virtual Environment**: Located in `venv/` directory
- **IDE**: IntelliJ IDEA project setup

## Common Commands

To activate the virtual environment:
```bash
# Windows
venv\Scripts\activate

# Unix/Linux/macOS
source venv/bin/activate
```

To install dependencies (once requirements are defined):
```bash
pip install -r requirements.txt
```

## Current State

This project appears to be in initial setup phase with no source code, dependencies, or configuration files present yet. The virtual environment is ready for development.

## Workflow

1. First think through the problem, read the codebase for relevant files, and write a plan to tasks/todo.md.
2. The plan should have a list of todo items that you can check off as you complete them
3. Before you begin working, check in with me and I will verify the plan.
4. Then, begin working on the todo items, marking them as complete as you go.
5. Every step of the way just give me a high level explanation of what changes you made
6. Make every task and code change you do as simple as possible. We want to avoid making any massive or complex changes. Every change should impact as little code as possible. Everything is about simplicity.
7. Make sure to not create large Python files. Follow SOLID principles to break big components to smaller ones.
8. Once finished, add the new files to git staging
9. Finally, add a review section to the todo.md file with a summary of the changes you made and any other relevant information.