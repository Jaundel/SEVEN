# SEVEN

SEVEN (Sustainable Energy Via Efficient Neural-routing) addresses the critical inefficiency in modern AI systems: with an estimated 10 billion daily AI queries globally, current deployments consume approximately 1,277 gigawatt-hours annually by routing all requests through energy-intensive cloud infrastructure regardless of complexity. A single cloud inference consumes 0.35 watt-hours, yet OpenAI's 2025 usage study shows that approximately 40% of queries are simple factual lookups or text transformations that could execute locally using just 0.02 watt-hours—a 94% reduction per query. SEVEN implements an intelligent classification layer that directs factual queries to lightweight local models, computational tasks to direct APIs, and reserves cloud resources for the 60% of queries genuinely requiring sophisticated reasoning. At global scale, this architectural approach could save 583 gigawatt-hours annually—enough to power 54,000 homes for a year or equivalent to a 290-megawatt power plant running continuously. By tracking and reporting energy consumption per query, SEVEN demonstrates that intelligent routing can achieve grid-scale energy savings, directly advancing UN Sustainable Development Goal 7: Affordable and Clean Energy.

## Tech Stack

- Language: Python 3.12.10
- Local Runtime: Lemonade Server (hybrid NPU/GPU/CPU inference) with small language models (1B-3B parameters recommended)
- Cloud Fallback: Groq (Llama 3 70B) or OpenAI GPT-4o-mini
- Libraries: `openai`, `groq`, `requests`, `rich`, `pyyaml`, `python-dotenv`

## Setup

See `SETUP.md` for the full installation and configuration checklist, including Lemonade Server installation, local model pulls, and environment variable details.

## Team Roles & Files

- Jaundel — Local Model Developer — `local_model.py`: Integrate Lemonade Server, send prompts to local small language models, and return responses with retry logic.
- Samin — Cloud Developer — `cloud_model.py`: Manage Groq/OpenAI credentials, forward prompts to cloud backends, and normalize replies.
- Yusuf — Router/Classifier Developer — `router.py`, `prompts.py`: Classify EASY/HARD/UNSAFE prompts, choose the right model, and manage prompt templates plus guardrails.
- Hamanpreet — Energy/Timer Developer — `energy.py`: Track runtime, estimate energy in Wh, and highlight savings vs. cloud-only runs.
- Aadil — CLI/Display Developer — `main.py`: Provide the terminal UX, gather user input, call the router, and display results plus energy metrics.

## Documentation & Collaboration

- Every Python file starts with the shared SEVEN header block (file, project, description, authors, date) plus a module-level docstring for quick context.
- Functions follow Google-style docstrings including Args/Returns/Raises/TODO to keep contracts explicit across teammates.
- Inline comments explain “why” decisions, and each module stays independently testable while work moves through branches and pull requests so ownership remains equal.

# Project Seven CLI

## Requirements

- Python 3.x
- Install pyfiglet:
  pip install pyfiglet
  pip install rich

## Run the CLI script

python cli.py
