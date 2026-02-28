# EcoOptima Agentic Workflow

## General Information

This project utilizes OpenAI's [Agents SDK](https://openai.github.io/openai-agents-python/) to create a custom agentic workflow for the following frameworks:

**Community:** Visual MACCs for a prototype using optimized plant bundles (“Lego-style”) with digital tools and MACCs at the site selected.

**Consumer:** Visual MACCs for green purchasing, EV adoption, energy star, solar, etc.

**Business:** Visual MACCs for energy efficiency, CCS, DAC, and operations. This requires an understanding of the entire value chain.

**Government:** Visual MACCs for tax and incentive policy to scale carbon removal.

**Academic:** Visual MACCs for sustainability research, teaching, and workforce impact.

## Capabilities

This workflow is able to:

- Take in a user query in the terminal
- Use a guardrail to reject off-topic question
- Triage the query and hand it off to a specialized response agent
- Enable the response agents to use both custom and built-in tools (file search, plotting) to generate responses
- Save any charts and respond to the user in the web interface

## Setup

To run this code on your machine, complete the following steps:

1. Clone this repo with `git clone https://github.com/anthonyrohloff/ecooptima-agentic-workflow.git`.

2. Create a Python virtual environment and run `pip install openai-agents openai-agents[viz] matplotlib flask`.

3. Set your OpenAI API key in the terminal with `export OPENAI_API_KEY=sk-...` (on Linux).

4. Run the **app.py** file and try it out!

## Contributing

To ensure a smooth development environment, please adhere to the following rules for development:

1. Any time you notice an issue or think of a feature you want to implement, create an issue in GitHub. Give a detailed description of the issue/feature.

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
