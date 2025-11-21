from agents import Agent, FileSearchTool, InputGuardrail, GuardrailFunctionOutput, Runner, ItemHelpers
from agents.exceptions import InputGuardrailTripwireTriggered
from agents.extensions.visualization import draw_graph
from pydantic import BaseModel
import asyncio


# Import plotting tools
from ecooptima_tools import plot_bar_chart, plot_pie_chart


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
plant_benefits_agent = Agent(
    name="Planting Benefits Advisor",
    handoff_description="Specialist agent for quantifying planting benefits",
    instructions="""You quantify the environmental benefits (carbon sequestration and stormwater inception) for the list
                    of plants provided to you. Use the vector store file search tool to look up information about each plant 
                    given to you.
                    
                    Return your answer to the user as a detailed report with quantified benefits for each plant species. Feel
                    free to include tables and charts to illustrate your points if necessary.
                    
                    Always provide a rationale for your quantifications and cite relevant studies or data sources.""" + postfix,
    tools=[
        FileSearchTool(
            vector_store_ids=["vs_6910105ece0c81918f2371e0f6c32696"] # vector store ID for tree plant matrix
        ),
        plot_bar_chart,
        plot_pie_chart
    ]
)

class PlantSelection(BaseModel):
    plants: list[str]
    notes: str

plant_matrix_agent = Agent(
    name="Plant Matrix Advisor",
    handoff_description="Specialist agent for plant matrix",
    instructions="""You recommend the best plant species from the provided plant matrix, using only the FileSearchTool (no internet sources), 
                    based on the structured variables you receive. Enforce species diversity and resilience. When numeric comparisons are requested 
                    (height, canopy spread, growth rate, etc.), call the appropriate charting tool first.

                    Respond to the user with a ranked list of species, including size, survival probability, and maintenance costs.

                    After you produce your ranked list, immediately hand off to the Planting Benefits Advisor, passing only the plant names (no other details).
                    """ + postfix,
    output_type=PlantSelection,
    handoffs=[plant_benefits_agent], # TODO: it doesnt hand off for some reason - figure it out
    tools=[
        FileSearchTool(
            vector_store_ids=["vs_6910105ece0c81918f2371e0f6c32696"] # vector store ID for tree plant matrix
        ),
        plot_bar_chart,
        plot_pie_chart
    ]
)


# Define triage agent
triage_agent = Agent(
    name="Triage Agent",
    instructions="""You use the given query and map it to the following variables (leave any variables that are not mentioned in the query blank):
                    user_location = Cincinnati, Ohio
                    project_type = [what the desired project is (tiny forest, street trees, schoolyard, etc...)]
                    scale = [size of project (for a park, a neighborhood, a city, a university, etc...)]
                    time_horizon_years = [how long the user wants project SETUP will take, not including continuous maintenance]
                    budget = [total budget for project]
                    
                    Then, pass these variables to the plant_matrix_agent.
                    """,
    handoffs=[plant_matrix_agent],
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
            if user_input.strip().lower() == "exit":
                break

            #result = await Runner.run(triage_agent, input=user_input)

            result = Runner.run_streamed(
                triage_agent,
                input=user_input,
            )

            async for event in result.stream_events():
                # 1) When the current agent changes (e.g. Triage -> Plant Matrix -> Planting Benefits)
                if event.type == "agent_updated_stream_event":
                    print(f"\n[Now using agent: {event.new_agent.name}]\n")

                # 2) High-level items: messages, tool calls, tool outputs, etc.
                elif event.type == "run_item_stream_event":
                    item = event.item

                    if item.type == "tool_call_item":
                        print("\n[Tool was called]\n")

                    elif item.type == "tool_call_output_item":
                        print(f"\n[Tool output]: {item.output}\n")

                    elif item.type == "message_output_item":
                        # This is where you see the text from each agent
                        text = ItemHelpers.text_message_output(item)
                        agent_name = getattr(item.agent, "name", "Unknown agent")
                        print(f"\n--- Message from {agent_name} ---\n{text}\n")

            # Final answer
            print(result.final_output)

        except InputGuardrailTripwireTriggered as e:
            print("Guardrail blocked this input:", e)


if __name__ == "__main__":
    asyncio.run(main())