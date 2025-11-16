from agents import Agent, FileSearchTool, InputGuardrail, GuardrailFunctionOutput, Runner
from agents.exceptions import InputGuardrailTripwireTriggered
from agents.extensions.visualization import draw_graph
from pydantic import BaseModel
import asyncio

from ecooptima_tools import plot_tree_metric_bar_chart

postfix = " Provide your answer in plaintext with no bolding. The response is intended for a terminal interface."

class EcoOptimaOutput(BaseModel):
    is_eco_optima: bool
    reasoning: str

guardrail_agent = Agent(
    name="Guardrail check",
    instructions="Check if the user is asking about plants, unless the question is referencing a previous message.",
    output_type=EcoOptimaOutput,
)

tree_advisor_agent = Agent(
    name="Tree Advisor",
    handoff_description="Specialist agent for trees",
    instructions="""You give recommendations on the best trees to plant from the plant matrix file given to you. 
                When asked a question about plants, always refer to the file first. Avoid responding with plants from
                the internet if possible. Explain important characteristics and care instructions clearly in plaintext.
                When someone asks to visualize numeric comparisons (heights, canopy spread, growth rate, etc.),
                call the plot_tree_metric_bar_chart tool with the structured list of trees before answering.""" + postfix,
    tools=[
        FileSearchTool(
            vector_store_ids=["vs_6910105ece0c81918f2371e0f6c32696"]
        ),
        plot_tree_metric_bar_chart,
    ]
)

other_plants_advisor_agent = Agent(
    name="Other Plants Advisor",
    handoff_description="Specialist agent for other plants",
    instructions="You provide assistance with queries about various plants from the plant matrix file given to you. Explain important characteristics and care instructions clearly in plaintext." + postfix,
    tools=[
        FileSearchTool(
            vector_store_ids=["vs_6910105ece0c81918f2371e0f6c32696"]
        )
    ]
)
async def eco_optima_guardrail(ctx, agent, input_data):
    result = await Runner.run(guardrail_agent, input_data, context=ctx.context)
    final_output = result.final_output_as(EcoOptimaOutput)
    return GuardrailFunctionOutput(
        output_info=final_output,
        tripwire_triggered=not final_output.is_eco_optima,
    )

triage_agent = Agent(
    name="Triage Agent",
    instructions="You determine which agent to use based on the user's question.",
    handoffs=[other_plants_advisor_agent, tree_advisor_agent],
    input_guardrails=[
        InputGuardrail(guardrail_function=eco_optima_guardrail),
    ],
)

draw_graph(triage_agent, filename="agent_graph")

async def main():
    # Example 1: Eco-optimal question
    while True:
        try:
            user_input = input("")
            if user_input.strip() == "exit":
                break
            result = await Runner.run(triage_agent, user_input)
            print(result.final_output)
        except InputGuardrailTripwireTriggered as e:
            print("Guardrail blocked this input:", e)

    # Example 2: General/philosophical question
    # try:
    #     result = await Runner.run(triage_agent, "What is the meaning of life?")
    #     print(result.final_output)
    # except InputGuardrailTripwireTriggered as e:
    #     print("Guardrail blocked this input:", e)

if __name__ == "__main__":
    asyncio.run(main())
