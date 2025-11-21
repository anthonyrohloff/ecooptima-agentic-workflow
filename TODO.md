# TODO

Generated from open GitHub issues.

## enhancement

- [#9] Follow Community_GPT_Agent_Structure document for MVP implementation
  The document is located in the shared Google Drive.
  
  The proposed structure is:
  ```
  Input Agent -> Plant Matrix Agent -> Planting Benefits Agent  -> Dashboard Agent
                                  \                        /
                                                              -> Local ROI Agent ->
  ```
  
  ---
  
  **Input Agent**
  This agent will set variable for the rest of the agents to use. It also has a guardrail built-in to filter out any non-EcoOptima related queries.
  
  user_location, project_type (tiny forest, street trees, park, schoolyard), scale, time_horizon_years, equity_priorities, and budget.
  
  ---
  
  **Plant Matrix Agent**
  This agent will give on the best plants to use from the plant matrix file given to it based on the user's query and the structured list of variables passed to it, enforcing species diversity and resilience. It will output a ranked list of species with fields for size, survival probability, and maintenance costs.
  
  ---
  
  **Planting Benefits Agent**
  This agent will quantify environmental benefits (carbon, stormwater) based on planting plans.
  
  It should:
  1. Estimate carbon sequestration and storage over time
  2. Calculate stormwater interception and infiltration benefits
  
  ---
  
  **Local ROI Agent**
  This agent will translate benefits into local ROI (health, heat) based on planting plans.
  
  It has 3 components:
  1. Health Benefits: quantify air quality and well-being impacts
  2. Heat Reduction: estimate localized cooling and cost savings

- [#10] Update Plant Matrix
  Expand/recreate plant matrix file to contain:
  
  - Carbon sequestration/year
  - Water retention date
  - Estimated “heat island” effect reduction
  - Synergistic relationships with other plants in the matrix/native/surrounding plants
  - Estimated maintenance costs and/or tasks
  - More plants (Optional)
  
  in addition to all of the columns it contains now.

## new-feature

- [#1] Enable "conversations" with agents - not just one-line interactions
  Currently, the program works like this:
  
  1. You run the program and are prompted with a blank terminal
  2. You input a question into the terminal and the guardrail_agent checks it for validity, then hands it to the triage_agent
  3. The triage_agent delegates to either the tree_advisor_agent or the other_plants_advisor_agent, and that agent answers your question 
  4. If you input another question string now, you jump back to step 2. The agents have no recollection of your previous query.
  
  The task at hand is to figure out how to have a conversation with the tree_advisor_agent and the other_plants_advisor_agent for as long as the user wants. Then, they should also be able to "reset" back to the start of the workflow if desired.

- [#15] Log responses for easy review
  The workflow's logs are able to be seen at https://platform.openai.com/logs, but to make it easy to see previous responses, we should implement a way to save the text response and charts from all agents.
  
  - Create a folder with the sligified title from ecooptima_tools.py
  - Put .txt files for each agent response and any charts created in the folder
  - Add top-level folder to .gitignore
  
  This will also help with #11 in that we will be able to easily see the information needed to solve that issue. Probably best to do this before #11.

## question

- [#11] Experiment with ways to reduce cost
  As of 11/26/2025, one run costs ~0.25 cents. This number will only go up as time goes on and the system expands. It would be good to do some research on what drives the cost (purely tokens used, I think), then see if some measures can be implemented to mitigate some of the cost per run.

