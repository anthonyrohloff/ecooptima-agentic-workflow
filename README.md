# EcoOptima Agentic Workflow

## General Information

This project utilized OpenAI's [Agents SDK](https://openai.github.io/openai-agents-python/) to create a custom agentic workflow for the following framework:

**Community-urban afforestation optimization** – Design natural plant bundles (like
“Legos”) for urban afforestation using digital technology, AI agents, and custom
GPTs, guided by MACCs, to maximize carbon absorption and enable scalable
implementation.

## Capabilities

As of 11/16/2025, this repo hosts a prototype of this framework with the structure in the graph below:

![Current Agent Structure](agent_graph.png)
*Current Agent Structure*

This workflow is able to:
- Take in a user query in the terminal
- Use a guardrail to reject off-topic question
- Triage the query and hand it off to a specialized response agent
- Enable the response agents to use both custom and built-in tools (file search, plotting) to generate responses
- Save any charts and respond to the user in the terminal

## Setup

To run this code on your machine, complete the following steps:

1. Clone this repo.

2. Create a Python virtual environment and run `pip install -r requirements.txt`.

3. Set your OpenAI API key in the terminal with `export OPENAI_API_KEY=sk-...`.

4. Run the **ecooptima.py** file and try it out!

## Contributing

To ensure a smooth development environment, please adhere to the following rules for development:

1. Any time you notice an issue or want to add a feature, please update the TODO.md and create an issue in GitHub. Give a detailed description of the issue/feature in GitHub.

2. Everything is a branch. No code changes should be made on the main branch. Anytime you want to modify the code, use `git checkout -b [your-branch-name]`.

Then, when your code committed to your branch and ready to be merged, perform the following process:

1. Check off the item in TODO.md.

2. `git checkout [your-branch-name]`

3. `git pull origin main`

4. `git push -u origin [your-branch-name]`

5. Open GitHub and find the "Compare & Pull Request" button at the top of the "Code" page.

6. Describe the code being merged and add something like `Resolves #12` where "#12" is the number of the issue that was opened in GitHub. Delete your branch from the GitHub repo after this is done (the option will appear).