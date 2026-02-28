from typing import List
from pydantic import BaseModel
from agents import (
    Agent,
    Runner,
    InputGuardrail,
    GuardrailFunctionOutput,
    RunContextWrapper,
    FileSearchTool,
)

from ecooptima_tools import plot_bar_chart


class CommunityWorkflow:
    #################
    # CONFIG / INIT #
    #################

    def __init__(
        self,
        agent_model: str = "gpt-5-nano",
        plant_matrix_vector_store: str = "vs_6910105ece0c81918f2371e0f6c32696",
    ):
        self.agent_model = agent_model
        self.plant_matrix_vector_store = plant_matrix_vector_store

        # Initialize agents
        self.local_roi_agent = self._build_local_roi_agent()
        self.conversational_agent = self._build_conversational_agent()
        self.guardrail_agent = self._build_guardrail_agent()
        self.plant_matrix_agent = self._build_plant_matrix_agent()

    ########################
    # SHARED DATA MODELS  #
    ########################

    class RankedSpecies(BaseModel):
        species: str
        size: str
        survivial_probability: str
        maintenance_costs: str

    class PlantMatrixResult(BaseModel):
        rankings: List["CommunityWorkflow.RankedSpecies"]

    class GuardrailOutput(BaseModel):
        is_eco_optima: bool
        reasoning: str

    #################
    # HOOKS / UTILS #
    #################

    async def on_handoff(self, ctx: RunContextWrapper[None], input_data):
        print(input_data)

    async def eco_optima_guardrail(self, ctx, agent, input_data):
        result = await Runner.run(self.guardrail_agent, input_data)
        final_output = result.final_output_as(self.GuardrailOutput)

        return GuardrailFunctionOutput(
            output_info=final_output,
            tripwire_triggered=not final_output.is_eco_optima,
        )

    ####################
    # AGENT BUILDERS  #
    ####################

    def _build_local_roi_agent(self) -> Agent:
        return Agent(
            name="Local ROI Advisor",
            model=self.agent_model,
            instructions="""Quantify the air quality and well-being impacts of planting the given list of plants.
                            Estimate urban heat island mitigation, environmental benefits, and cooling cost savings.
                            Plot a marginal abatement cost curve for carbon sequestration using plot_bar_chart.

                            REQUIREMENTS:
                            1. Return a plaintext response with findings, ranked list, and takeaways.
                            2. Create a MACC using plot_bar_chart with no explanation.""",
            output_type=str,
            tools=[
                FileSearchTool(vector_store_ids=[self.plant_matrix_vector_store]),
                plot_bar_chart,
            ],
        )

    def _build_conversational_agent(self) -> Agent:
        return Agent(
            name="Conversational Agent",
            model=self.agent_model,
            instructions="""You are the user-facing assistant for EcoOptima follow-up questions.
                            Use latest_workflow_output as factual context.""",
            output_type=str,
        )

    def _build_guardrail_agent(self) -> Agent:
        return Agent(
            name="Guardrail",
            model=self.agent_model,
            instructions="""Check if the user is asking about plants.
                            Return a boolean and one-sentence reasoning.""",
            output_type=self.GuardrailOutput,
        )

    def _build_plant_matrix_agent(self) -> Agent:
        return Agent(
            name="Plant Matrix Advisor",
            model=self.agent_model,
            handoff_description="Specialist agent for plant matrix",
            instructions="""Recommend the best plant species using the plant matrix.
                            Enforce species diversity and resilience.""",
            tools=[
                FileSearchTool(vector_store_ids=[self.plant_matrix_vector_store]),
            ],
            input_guardrails=[
                InputGuardrail(guardrail_function=self.eco_optima_guardrail)
            ],
            output_type=self.PlantMatrixResult,
        )

    #################
    # WORKFLOW RUN #
    #################

    async def run(self, user_input: str):
        result = await Runner.run(self.plant_matrix_agent, user_input)
        result = await Runner.run(
            self.local_roi_agent,
            result.final_output.model_dump_json(),
        )
        return result
