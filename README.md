# EcoOptima Agentic Workflow

## General Information

This project utilizes OpenAI's [Agents SDK](https://openai.github.io/openai-agents-python/) to create a custom agentic workflow for the following framework:

**Community-urban afforestation optimization** – Design natural plant bundles (like
“Legos”) for urban afforestation using digital technology, AI agents, and custom
GPTs, guided by MACCs, to maximize carbon absorption and enable scalable
implementation.

## Capabilities

This repo hosts a prototype of this framework with the structure in the graph below:

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

1. Clone this repo with `git clone https://github.com/anthonyrohloff/ecooptima-agentic-workflow.git`.

2. Create a Python virtual environment and run `pip install openai-agents openai-agents[viz] graphviz matplotlib`.

3. Set your OpenAI API key in the terminal with `export OPENAI_API_KEY=sk-...`.

4. Install [Graphviz](https://graphviz.org/download/).

5. Run the **app.py** file and try it out!

## Contributing

To ensure a smooth development environment, please adhere to the following rules for development:

1. Any time you notice an issue or think of a feature you want to implement, create an issue in GitHub. Give a detailed description of the issue/feature. GitHub Actions will **automatically** update the TODO.md file for easy reference while developing. **DO NOT touch TODO.md**.

2. Everything is a branch. No code changes should be made on the main branch. Anytime you want to modify the code, use `git checkout -b [your-branch-name]`, make your changes there, then commit and merge.

To commit your code to Git, do the following:

1. `git status` to see all modified files.

2. `git add .` to add all modifications OR add files manually with `git add [your-file-name]`.

3. `git commit -m "[your-commit-message]"` to commit the changes to Git.

Then, when your code committed to your branch and ready to be merged, perform the following process:

1. `git checkout [your-branch-name]`

2. `git pull origin main`

3. `git push -u origin [your-branch-name]`

4. Open GitHub and find the "Compare & Pull Request" button at the top of the "Code" page.

5. Describe the code being merged and add something like `Resolves #12` where "#12" is the number of the issue that was opened in GitHub. Delete your branch from the GitHub repo after this is done (the option will appear).
