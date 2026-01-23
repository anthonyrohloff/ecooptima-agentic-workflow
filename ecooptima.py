from agents import (
    Agent,
    FileSearchTool,
    InputGuardrail,
    GuardrailFunctionOutput,
    Runner,
    ItemHelpers,
)
from agents.exceptions import InputGuardrailTripwireTriggered
from agents.extensions.visualization import draw_graph
from pydantic import BaseModel
from pathlib import Path
import os
import asyncio


# Import plotting tools
from ecooptima_tools import plot_bar_chart, plot_pie_chart, _generate_timestamp


# Common postfix for agent instructions
postfix = " Provide your answer in plaintext with no bolding. The response is intended for a terminal interface. Always start your answer with your name."

# Model each acgent will use
agent_model = "gpt-5-nano"


# Response logging structure
class RunLog:
    timestamp: str
    input: str
    response: str


# TypedDict for guardrail output
class EcoOptimaOutput(BaseModel):
    is_eco_optima: bool  # whether the input is related to plants
    reasoning: str  # reasoning for the determination


# Define guardrail agent: https://openai.github.io/openai-agents-python/guardrails/
guardrail_agent = Agent(
    name="Guardrail check",
    model=agent_model,
    instructions="Check if the user is asking about plants. Output a one sentence response classifying it as related to EcoOptima or not.",
    output_type=EcoOptimaOutput,
)


# Define guardrail function
async def eco_optima_guardrail(ctx, agent, input_data):
    result = await Runner.run(
        guardrail_agent, input_data, context=ctx.context
    )  # pass context to maintain conversation history [TODO: Enable "conversations" with agents - not just one-line interactions]
    # although, guardrail checks may not need context - this should be investigated
    final_output = result.final_output_as(
        EcoOptimaOutput
    )  # parse final output as EcoOptimaOutput

    # Check if tripwire was triggered and return appropriate GuardrailFunctionOutput
    return GuardrailFunctionOutput(
        output_info=final_output,
        tripwire_triggered=not final_output.is_eco_optima,
    )


# Define specialist agents
local_roi_agent = Agent(
    name="Local ROI Advisor",
    model=agent_model,
    handoff_description="Specialist agent for translating benefits into local ROI (health, heat) based on planting plans.",
    instructions="""Quantify the air quality and well-being impacts of planting the given list of plants. Also, estimate the urban heat 
                    island mitigation benefits based on adding canopy cover to an urban environment. Extrapolate this estimate to cost 
                    savings on cooling costs for nearby buildings. 
                    
                    Return the finalized list to the user along with any charts or tables necessary to illustrate your points. Use the 
                    plot_bar_chart and plot_pie_chart tools as necessary to visualize comparisons of planting benefits."""
    + postfix,
    tools=[
        FileSearchTool(
            vector_store_ids=[
                "vs_6910105ece0c81918f2371e0f6c32696"
            ]  # vector store ID for tree plant matrix
        ),
        plot_bar_chart,
        plot_pie_chart,
    ],
)


# Define specialist agents
plant_benefits_agent = Agent(
    name="Planting Benefits Advisor",
    model=agent_model,
    handoff_description="Specialist agent for quantifying planting benefits",
    instructions="""You quantify the environmental benefits (carbon sequestration and stormwater inception) for the list
                    of plants provided to you. Use the vector store file search tool to look up information about each plant 
                    given to you.
                    
                    Add your input to the given list and hand it off to the local_roi_agent. Do not give a final response to the user. Feel
                    free to include tables and charts to illustrate your points if necessary by using the plot_bar_chart and plot_pie_chart tools 
                    you have access to."""
    + postfix,
    handoffs=[local_roi_agent],
    tools=[
        FileSearchTool(
            vector_store_ids=[
                "vs_6910105ece0c81918f2371e0f6c32696"
            ]  # vector store ID for tree plant matrix
        ),
        plot_bar_chart,
        plot_pie_chart,
    ],
)


class PlantSelection(BaseModel):
    plants: list[str]
    notes: str


plant_matrix_agent = Agent(
    name="Plant Matrix Advisor",
    model=agent_model,
    handoff_description="Specialist agent for plant matrix",
    instructions="""You recommend the best plant species from the provided plant matrix, using only the FileSearchTool (no internet sources), 
                    based on the structured variables you receive. Enforce species diversity and resilience. When numeric comparisons are requested 
                    (height, canopy spread, growth rate, etc.), call the appropriate charting tool first.

                    Create a ranked list of species, including size, survival probability, and maintenance costs.

                    After you produce your ranked list, immediately hand off to the Planting Benefits Advisor, passing only the list produced.
                    Do not give a final response to the user."""
    + postfix,
    output_type=PlantSelection,
    handoffs=[
        plant_benefits_agent
    ],  # TODO: it doesnt hand off for some reason - figure it out
    tools=[
        FileSearchTool(
            vector_store_ids=[
                "vs_6910105ece0c81918f2371e0f6c32696"
            ]  # vector store ID for tree plant matrix
        ),
        plot_bar_chart,
        plot_pie_chart,
    ],
)


# Define triage agent
triage_agent = Agent(
    name="Triage Agent",
    model=agent_model,
    instructions="""You use the given query and map it to the following variables (leave any variables that are not mentioned in the query blank):
                    user_location = Cincinnati, Ohio
                    project_type = [what the desired project is (tiny forest, street trees, schoolyard, etc...)]
                    scale = [size of project (for a park, a neighborhood, a city, a university, etc...)]
                    time_horizon_years = [how long the user wants project SETUP will take, not including continuous maintenance]
                    budget = [total budget for project]
                    
                    Then, pass any variables you fill to the plant_matrix_agent.
                    """,
    handoffs=[plant_matrix_agent],
    input_guardrails=[
        InputGuardrail(
            guardrail_function=eco_optima_guardrail
        ),  # attach the eco_optima_guardrail to the triage agent
    ],
)


# Visualize agent graph using Graphviz: https://openai.github.io/openai-agents-python/visualization/
draw_graph(triage_agent, filename="agent_graph")


# Main function to run the agent
async def main(user_text):
    while True:
        try:
            user_input = user_text

            # Exit condition
            if user_input.strip().lower() == "exit":
                break

            RunLog.timestamp = _generate_timestamp()
            log_dir = Path("response_log") / RunLog.timestamp
            log_dir.mkdir(parents=True, exist_ok=True)
            os.environ["ECOOPTIMA_LOG_DIR"] = str(log_dir)

            result = await Runner.run(triage_agent, input=user_input)

            # Note: streamed execution is currently disabled due to some issues with the SDK.
            # This is a good way to test, but may not work as expected in all cases.
            # Use the non-streamed version above for reliable results.

            # result = Runner.run_streamed(
            #     triage_agent,
            #     input=user_input,
            # )

            # async for event in result.stream_events():
            #     # 1) When the current agent changes (e.g. Triage -> Plant Matrix -> Planting Benefits)
            #     if event.type == "agent_updated_stream_event":
            #         print(f"\n[Now using agent: {event.new_agent.name}]\n")

            #     # 2) High-level items: messages, tool calls, tool outputs, etc.
            #     elif event.type == "run_item_stream_event":
            #         item = event.item

            #         if item.type == "tool_call_item":
            #             print("\n[Tool was called]\n")

            #         elif item.type == "tool_call_output_item":
            #             print(f"\n[Tool output]: {item.output}\n")

            #         elif item.type == "message_output_item":
            #             # This is where you see the text from each agent
            #             text = ItemHelpers.text_message_output(item)
            #             agent_name = getattr(item.agent, "name", "Unknown agent")
            #             print(f"\n--- Message from {agent_name} ---\n{text}\n")

            # Final answer
            print(result.final_output)
            return result.final_output

        except InputGuardrailTripwireTriggered as e:
            print("Guardrail blocked this input:", e)
            return str(e)

        # Log the run
        # TODO: fix logging - we don't get any now that we return stuff in this function
        RunLog.input = user_input
        RunLog.response = result.final_output
        (log_dir / "input.txt").write_text(RunLog.input, encoding="utf-8")
        (log_dir / "output.txt").write_text(RunLog.response, encoding="utf-8")


# if __name__ == "__main__":
#     asyncio.run(main())
