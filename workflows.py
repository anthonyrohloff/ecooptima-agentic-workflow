from typing import List, Literal, Any
from pydantic import BaseModel, Field
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


HouseholdArchetype = Literal["SFH_owner", "apartment_renter", "mixed"]


class ConsumerWorkflow:
    #################
    # CONFIG / INIT #
    #################

    def __init__(
        self,
        agent_model: str = "gpt-5-nano",
        consumer_vector_store: str = "vs_69a4d21889888191b4c0f0653a1f29e3",
    ):
        self.agent_model = agent_model
        self.consumer_vector_store = consumer_vector_store

        # Initialize agents
        self.consumer_macc_agent = self._build_consumer_macc_agent()
        self.consumer_roi_agent = self._build_consumer_roi_agent()
        self.conversational_agent = self._build_conversational_agent()

    ########################
    # SHARED DATA MODELS   #
    ########################

    class OptionRow(BaseModel):
        option_id: str
        category: str
        description: str

        # Effects
        annual_abatement_tCO2e: float = Field(..., ge=0)
        lifetime_years: int = Field(..., ge=1)
        lifetime_abatement_tCO2e: float = Field(..., ge=0)

        # Economics (consumer)
        net_present_cost_usd: float
        cost_per_tCO2e_usd: float

        # Practicality
        homeowner_feasible: bool
        renter_feasible: Literal[True, False, "Limited"]

        notes: str = ""

    class MaccAssumptions(BaseModel):
        location: str = "Cincinnati, Ohio"
        household_archetype: HouseholdArchetype = "mixed"
        discount_rate_real: float = 0.04
        grid_emissions_basis: str = "Documented/assumed Cincinnati grid intensity"
        key_notes: List[str] = []

    class MaccResult(BaseModel):
        assumptions: "ConsumerWorkflow.MaccAssumptions"
        options: List["ConsumerWorkflow.OptionRow"]
        sorted_option_ids: List[str]
        cumulative_abatement_tCO2e: List[float]
        narrative: str

    #################
    # HOOKS / UTILS #
    #################

    async def on_handoff(self, ctx, input_data: Any):
        print(input_data)

    ####################
    # AGENT BUILDERS   #
    ####################

    def _build_consumer_macc_agent(self):
        return Agent(
            name="Consumer MACC Advisor",
            model=self.agent_model,
            instructions="""Recommend the best consumer climate actions for a Cincinnati household using a marginal abatement cost curve.
                            Build 8-15 actions covering purchases, transport, home energy, efficiency, and behavior.
                            For each action, estimate annual and lifetime abatement, net present cost, cost per tCO2e, and homeowner/renter feasibility.
                            Enforce internally consistent assumptions, avoid double counting, sort by cost_per_tCO2e_usd ascending,
                            and compute cumulative_abatement_tCO2e in that order.""",
            output_type=self.MaccResult,
            tools=[
                FileSearchTool(vector_store_ids=[self.consumer_vector_store]),
            ],
        )

    def _build_consumer_roi_agent(self) -> Agent:
        return Agent(
            name="Consumer ROI Advisor",
            model=self.agent_model,
            instructions="""Quantify the household cost and emissions impacts of the given consumer MACC options.
                            Estimate which actions are cheapest, which deliver the most abatement, and which are limited by renter versus homeowner status.
                            Plot a bar chart for cost_per_tCO2e_usd using plot_bar_chart.

                            REQUIREMENTS:
                            1. Return a plaintext response with findings, ranked list, and takeaways.
                            2. Create a bar chart using plot_bar_chart with no explanation.""",
            output_type=str,
            tools=[plot_bar_chart],
        )

    def _build_conversational_agent(self):
        return Agent(
            name="Consumer MACC Conversational Agent",
            model=self.agent_model,
            instructions="""
                            You are the user-facing assistant for EcoOptima follow-up questions.
                            Use latest_workflow_output as factual context.
                            """,
            output_type=str,
        )

    #################
    # WORKFLOW RUN  #
    #################

    async def run(self, user_input: str):
        result = await Runner.run(self.consumer_macc_agent, user_input)
        result = await Runner.run(
            self.consumer_roi_agent,
            result.final_output.model_dump_json(),
        )
        return result
