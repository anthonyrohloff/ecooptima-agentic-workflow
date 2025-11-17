from agents import Agent, FileSearchTool, InputGuardrail, GuardrailFunctionOutput, Runner
from agents.exceptions import InputGuardrailTripwireTriggered
from agents.extensions.visualization import draw_graph
from pydantic import BaseModel
import asyncio


# Import plotting tools
from ecooptima_tools import plot_tree_metric_bar_chart, plot_tree_metric_pie_chart


# Common postfix for agent instructions
postfix = " Provide your answer in plaintext with no bolding. The response is intended for a terminal interface. Always start your answer with your name."


# TypedDict for guardrail output
class EcoOptimaOutput(BaseModel):
    is_eco_optima: bool # whether the input is related to plants
    reasoning: str      # reasoning for the determination


# Define guardrail agent: https://openai.github.io/openai-agents-python/guardrails/
guardrail_agent = Agent(
    name="Guardrail check",
    instructions="Check if the user is asking about plants, unless the question is referencing a previous message.",
    output_type=EcoOptimaOutput,
)


# Define guardrail function
async def eco_optima_guardrail(ctx, agent, input_data):
    result = await Runner.run(guardrail_agent, input_data, context=ctx.context) # pass context to maintain conversation history [TODO: Enable "conversations" with agents - not just one-line interactions]
                                                                                # although, guardrail checks may not need context - this should be investigated
    final_output = result.final_output_as(EcoOptimaOutput) # parse final output as EcoOptimaOutput

    # Check if tripwire was triggered and return appropriate GuardrailFunctionOutput
    return GuardrailFunctionOutput(
        output_info=final_output,
        tripwire_triggered=not final_output.is_eco_optima,
    )


# Define specialist agents
plant_matrix_agent = Agent(
    name="Plant Matrix Advisor",
    handoff_description="Specialist agent for plant matrix",
    instructions="""You give recommendations on the best plant species to use from the plant matrix file given to you
                    based on the user's query and the structured list of variables passed to you. Enforce species diversity 
                    and resilience. 
                
                    When asked a question about plants, always refer to the file by using the provided FileSearchTool. 
                    Avoid responding with plants from the internet. 
                
                    When someone asks to visualize numeric comparisons (heights, canopy spread, growth rate, etc.), call the proper 
                    charting tool with the structured list of plants before answering.

                    In your answer include a ranked list of species with fields for size, survival probability, maintenance costs, 
                    and benefit coefficients (carbon, stormwater, energy savings).""" + postfix,
    tools=[
        FileSearchTool(
            vector_store_ids=["vs_6910105ece0c81918f2371e0f6c32696"] # vector store ID for tree plant matrix
        ),
        plot_tree_metric_bar_chart,
        plot_tree_metric_pie_chart
    ]
)


# Define triage agent
triage_agent = Agent(
    name="Triage Agent",
    instructions="""You use the given query and map it to the following variables (leave any variables that are not mentioned in the query blank):
                    user_location = [where the user is planning a project (use Cincinnati, OH as default if not specified)]
                    project_type = [what the desired project is (tiny forest, street trees, schoolyard, etc...)]
                    scale = [size of project (for a park, a neighborhood, a city, a university, etc...)]
                    time_horizon_years = [how long the user wants project SETUP will take, not including continuous maintenance]
                    equity_priorities = [Needs (canopy gap, heat vulnerability, asthma, income, renter ratio, etc...), Access (number of users), Process (community engagement, multilingual materials, local hiring, stewardship, etc...), and Recognition (cultural or historical considerations)],
                    budget = [total budget for project]
                    
                    Then, pass the query and these variables to the plant_matrix_agent.
                    """,
    handoffs=[plant_matrix_agent], # list of specialist agents to hand off to
    input_guardrails=[
        InputGuardrail(guardrail_function=eco_optima_guardrail), # attach the eco_optima_guardrail to the triage agent
    ],
)


# Visualize agent graph using Graphviz: https://openai.github.io/openai-agents-python/visualization/
draw_graph(triage_agent, filename="agent_graph")


# Main function to run the agent
async def main():
    while True:
        try:
            user_input = input("Input your query (or type 'exit' to quit): ")
            
            # Exit condition
            if user_input.strip() == "exit":
                break
            
            result = await Runner.run(triage_agent, user_input)
            print(result.final_output)
        except InputGuardrailTripwireTriggered as e:
            print("Guardrail blocked this input:", e)

if __name__ == "__main__":
    asyncio.run(main())
