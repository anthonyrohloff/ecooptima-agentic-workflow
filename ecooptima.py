from agents import (
    Agent,
    FileSearchTool,
    InputGuardrail,
    GuardrailFunctionOutput,
    Runner,
    RunContextWrapper,
    handoff,
)
from agents.exceptions import InputGuardrailTripwireTriggered
from agents.extensions.visualization import draw_graph
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from pydantic import BaseModel
import asyncio
from pathlib import Path
import os
import json


# Import plotting tools
from ecooptima_tools import plot_bar_chart, _generate_timestamp  # , plot_pie_chart


###############
### GLOBALS ###
###############


# Model each acgent will use
agent_model = "gpt-5-nano"

# Vector store ID for the plant matrix file on the OpenAI Platform
plant_matrix_vector_store = "vs_6910105ece0c81918f2371e0f6c32696"


# Optional function to perform an action on handoff - keeping as an example for now
async def on_handoff(ctx: RunContextWrapper[None], input_data):
    print(input_data)


# Structured output base class
# Used by plant_matrix_agent and extended by planting_benefits_agent
class RankedSpecies(BaseModel):
    species: str
    size: str
    survivial_probability: str
    maintenance_costs: str


#######################
### LOCAL ROI AGENT ###
#######################


# class RankedSpeciesForROI(RankedSpecies):
#     carbon_sequestration: str
#     stormwater_inception: str
#     heat_island_mitigation: str
#     air_quality_benefit: str
#     well_being_benefit: str
#     cooling_cost_savings: str
#     carbon_sequestration: str
#     stormwater_inception: str
#
#
#
# class LocalROIResult(BaseModel):
#     rankings: list[RankedSpeciesForROI]


local_roi_agent = Agent(
    name="Local ROI Advisor",
    model=agent_model,
    instructions="""Quantify the air quality and well-being impacts of planting the given list of plants. Also, estimate the urban heat 
                    island mitigation benefits based on adding canopy cover to an urban environment. Estimate the environmental 
                    benefits (carbon sequestration and stormwater inception). Extrapolate this estimate to cost savings on 
                    cooling costs for nearby buildings. Use the data you have to plot a marginal abatement cost curve with the plot_bar_chart tool
                    to identify the most cost-effective plants for sequestration of carbon.

                    REQUIREMENTS:
                    1. Return a plaintext, summarized response about your findings. Your response should include three sections:
                       a brief paragraph explaining what the findings include, the ranked list in plaintext WITH their corresponding values 
                       for each category, and practical takeaways. No other notes, totals, explanaitions, or follow-up questions are allowed.
                    2. Create a MACC using the plot_bar_chart tool. IMPORTANT: do not explain the chart OR tell the user where it was saved to. 
                       Assume it will be automatically displayed and understood.""",
    output_type=str,
    tools=[
        FileSearchTool(vector_store_ids=[plant_matrix_vector_store]),
        plot_bar_chart,
        # plot_pie_chart,
    ],
)

#################################
### CONVERSATIONAL USER AGENT ###
#################################


conversational_agent = Agent(
    name="Conversational Agent",
    model=agent_model,
    instructions="""You are the user-facing assistant for EcoOptima follow-up questions.
                    You will receive a JSON payload with:
                    - latest_workflow_output: the most recent output from the local ROI workflow
                    - chat_history: recent back-and-forth turns
                    - user_followup: the current follow-up question

                    Use the latest_workflow_output as your primary factual context, then use chat_history for continuity.
                    Answer only the user's follow-up. If context is missing, say what is missing briefly.""",
    output_type=str,
)


###############################
### PLANTING BENEFITS AGENT ###
###############################


# class RankedSpeciesForBenefits(RankedSpecies):
#     carbon_sequestration: str
#     stormwater_inception: str
#
#
# class PlantingBenefitsResult(BaseModel):
#     rankings: list[RankedSpeciesForBenefits]
#
#
# local_roi_handoff = handoff(
#     agent=local_roi_agent, on_handoff=on_handoff, input_type=PlantingBenefitsResult
# )
#
#
# plant_benefits_agent = Agent(
#     name="Planting Benefits Advisor",
#     model=agent_model,
#     instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
#                     You quantify the environmental benefits (carbon sequestration and stormwater inception) for the list
#                     of plants provided to you. Use the vector store file search tool to look up information about each plant
#                     given to you.""",
#
#                     # Feel free to include tables and charts to illustrate your points if necessary by using
#                     # the plot_bar_chart tool you have access to.
#                     # Do NOT answer the user. Your ONLY output must be a single call to local_roi_handoff. After the tool call, stop.
#                     # Do NOT give a status update like 'request handed off to local roi agent.'""",
#     tools=[
#         FileSearchTool(vector_store_ids=[plant_matrix_vector_store]),
#         # plot_bar_chart,
#         # plot_pie_chart,
#     ],
#     # handoffs=[local_roi_handoff],
#     output_type=PlantingBenefitsResult,
# )

#######################
### GUARDRAIL AGENT ###
#######################


# TypedDict for guardrail output
class GuardrailOutput(BaseModel):
    is_eco_optima: bool  # whether the input is related to plants
    reasoning: str  # reasoning for the determination


# Define guardrail sub-agent: https://openai.github.io/openai-agents-python/guardrails/
guardrail_agent = Agent(
    name="Guardrail",
    model=agent_model,
    instructions="""Check if the user is asking about plants. 
                    Output a one sentence response classifying it as related to EcoOptima 
                    or not and a boolean value accordingly.""",
    output_type=GuardrailOutput,
)


# Define guardrail function to be called by the triage_agent
async def eco_optima_guardrail(ctx, agent, input_data):
    result = await Runner.run(guardrail_agent, input_data)
    final_output = result.final_output_as(GuardrailOutput)

    # Check if tripwire was triggered and return appropriate GuardrailFunctionOutput
    return GuardrailFunctionOutput(
        output_info=final_output,
        tripwire_triggered=not final_output.is_eco_optima,
    )


##########################
### PLANT MATRIX AGENT ###
##########################


class PlantMatrixResult(BaseModel):
    rankings: list[RankedSpecies]


# planting_benefits_handoff = handoff(
#     agent=plant_benefits_agent, on_handoff=on_handoff, input_type=PlantMatrixResult
# )

plant_matrix_agent = Agent(
    name="Plant Matrix Advisor",
    model=agent_model,
    handoff_description="Specialist agent for plant matrix",
    instructions="""You recommend the best plant species from the provided plant matrix by using the FileSearchTool at least once
                    based on the structured variables you receive. Enforce species diversity and resilience.

                    Create a ranked list of species, including size, survival probability, and maintenance costs.""",
    # Do NOT answer the user. Your ONLY output must be a single call to planting_benefits_handoff. After the tool call, stop.
    # Do NOT give a status update like 'request handed off to planting benefits advisor.'""",
    tools=[
        FileSearchTool(vector_store_ids=[plant_matrix_vector_store]),
        # plot_bar_chart,
        # plot_pie_chart,
    ],
    # handoffs=[planting_benefits_handoff],
    input_guardrails=[InputGuardrail(guardrail_function=eco_optima_guardrail)],
    output_type=PlantMatrixResult,
)


####################
### TRIAGE AGENT ###
####################


# Output structure to pass to plant_matrix_agent
# class InputVariables(BaseModel):
#     user_location: str | None = None
#     project_type: str | None = None
#     scale: str | None = None
#     time_horizon_years: str | None = None
#     budget: str | None = None
#
#
# # Handoff object to execute information relay
# plant_matrix_handoff = handoff(
#     agent=plant_matrix_agent, on_handoff=on_handoff, input_type=InputVariables
# )
#
#
# # Define triage agent
# triage_agent = Agent(
#     name="Triage Agent",
#     model=agent_model,
#     instructions="""
#                     You use the given query and map it to the following variables (leave any variables that are not mentioned in the query blank):
#                     user_location = Cincinnati, Ohio
#                     project_type = [what the desired project is (tiny forest, street trees, schoolyard, etc...)]
#                     scale = [size of project (for a park, a neighborhood, a city, a university, etc...)]
#                     time_horizon_years = [how long the user wants project SETUP will take, not including continuous maintenance]
#                     budget = [total budget for project] """,
#
#                     # Then, call the plant_matrix_handoff tool to pass the information to the next agent. Do not give a final response to the user.,
#     input_guardrails=[InputGuardrail(guardrail_function=eco_optima_guardrail)],
#     # handoffs=[plant_matrix_handoff],
#     output_type = InputVariables,
# )

############################
### GRAPHVIZ AND LOGGING ###
############################


# This is disabled becuase the current structure does not work with it
# Visualize agent graph using Graphviz: https://openai.github.io/openai-agents-python/visualization/
# draw_graph(triage_agent, filename="agent_graph")


# Response logging structure
class RunLog:
    timestamp: str
    input: str
    response: str


#####################
### MAIN FUNCTION ###
#####################


async def run_pipeline(user_input: str) -> str:
    RunLog.timestamp = _generate_timestamp()
    log_dir = Path("response_log") / RunLog.timestamp
    log_dir.mkdir(parents=True, exist_ok=True)
    os.environ["ECOOPTIMA_LOG_DIR"] = str(log_dir)

    result = await Runner.run(plant_matrix_agent, user_input)
    result = await Runner.run(local_roi_agent, result.final_output.model_dump_json())

    RunLog.input = user_input
    RunLog.response = result.final_output
    (log_dir / "input.txt").write_text(RunLog.input, encoding="utf-8")
    (log_dir / "output.txt").write_text(RunLog.response, encoding="utf-8")
    return result.final_output


def _trim_history(chat_history: list[dict], keep_last: int = 8) -> list[dict]:
    return chat_history[-keep_last:]


async def run_followup(user_input: str, session_state: dict) -> str:
    payload = {
        "latest_workflow_output": session_state.get("last_pipeline_output", ""),
        "chat_history": _trim_history(session_state.get("chat_history", [])),
        "user_followup": user_input,
    }
    result = await Runner.run(conversational_agent, json.dumps(payload))
    return result.final_output


# Main function to run either full workflow or conversational follow-up
async def main(user_text, mode: str = "analyze", session_state: dict | None = None):
    try:
        user_input = user_text

        if user_input.strip().lower() == "exit":
            return "exit"

        session_state = session_state if session_state is not None else {}
        session_state.setdefault("chat_history", [])

        if mode == "followup":
            if not session_state.get("last_pipeline_output"):
                return "No prior workflow context found. Run an analysis first, then ask a follow-up."
            response = await run_followup(user_input, session_state)
        else:
            response = await run_pipeline(user_input)
            session_state["last_pipeline_output"] = response

        session_state["chat_history"].append({"role": "user", "content": user_input})
        session_state["chat_history"].append({"role": "assistant", "content": response})
        session_state["chat_history"] = _trim_history(
            session_state["chat_history"], keep_last=12
        )

        return response

    except InputGuardrailTripwireTriggered as e:
        print("Guardrail blocked this input: ", e)
        return str(e)


if __name__ == "__main__":
    input = input("Query: ")
    result = asyncio.run(main(input))
    print(result)
