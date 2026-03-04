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


InstitutionType = Literal[
    "R1_research_university",
    "teaching_college",
    "community_college",
    "medical_center",
    "mixed",
]
Region = Literal["US", "EU", "UK", "Global"]


class AcademicWorkflow:
    #################
    # CONFIG / INIT #
    #################

    def __init__(
        self,
        agent_model: str = "gpt-5-nano",
        academic_vector_store: str = "vs_69a4d21889888191b4c0f0653a1f29e3",
    ):
        self.agent_model = agent_model
        self.academic_vector_store = academic_vector_store

        # State for follow-ups
        self.latest_workflow_output: "AcademicWorkflow.MaccResult"

        # Initialize agents (2 “thinking” agents + conversational)
        self.academic_macc_agent = self._build_academic_macc_agent()
        self.academic_roi_agent = self._build_academic_roi_agent()
        self.conversational_agent = self._build_conversational_agent()

    ########################
    # SHARED DATA MODELS   #
    ########################

    class AcademicOption(BaseModel):
        option_id: str
        category: Literal[
            "campus_operations", "research_programs", "workforce_training"
        ]
        description: str

        # Economics
        cost_usd: float
        lifetime_years: int = Field(..., ge=1, le=50)

        # Impact channels (tCO2e over lifetime)
        operational_abatement_tCO2e: float = Field(..., ge=0)
        research_spillover_tCO2e: float = Field(..., ge=0)
        workforce_spillover_tCO2e: float = Field(..., ge=0)

        # Derived fields (must be populated by the MACC agent)
        total_effective_abatement_tCO2e: float = Field(..., ge=0)
        cost_per_tCO2e_usd: float

        notes: str = ""

    class MaccAssumptions(BaseModel):
        institution_type: InstitutionType = "mixed"
        region: Region = "US"
        discount_rate_real: float = 0.04
        time_horizon_years: int = 20

        # Method notes (important for spillovers)
        research_attribution_method: str = "Expected-value: adoption_probability × plausible_global_abatement, discounted/allocated to institution"
        workforce_attribution_method: str = "Expected-value: graduates × career_years × impact_per_worker, attribution-adjusted"

        key_notes: List[str] = []

    class MaccResult(BaseModel):
        assumptions: "AcademicWorkflow.MaccAssumptions"
        options: List["AcademicWorkflow.AcademicOption"]

        # MACC ordering fields
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

    def _build_academic_macc_agent(self):
        return Agent(
            name="Academic MACC Advisor",
            model=self.agent_model,
            instructions="""
                            You build an academic-institution-focused marginal abatement cost curve (MACC) for climate mitigation.

                            DATA SOURCE:
                            - Use the academic vector store for option templates, typical costs, and any local priors.
                            - If the user provides institution details, tailor assumptions accordingly.

                            REQUIREMENTS:
                            1) Produce 8–15 options spanning ALL THREE categories:
                               - campus_operations (direct operational emissions)
                               - research_programs (knowledge spillovers)
                               - workforce_training (human capital / jobs spillovers)
                            2) For each option, fill:
                               - cost_usd, lifetime_years
                               - operational_abatement_tCO2e, research_spillover_tCO2e, workforce_spillover_tCO2e
                               - total_effective_abatement_tCO2e = sum of the three channels
                               - cost_per_tCO2e_usd = cost_usd / total_effective_abatement_tCO2e
                            3) Enforce internal consistency and avoid double counting:
                               - Do NOT count the same abatement in multiple channels for the same intervention.
                               - Research spillovers must be attribution-adjusted (expected value, conservative).
                               - Workforce spillovers must be attribution-adjusted and conservative.
                            4) Sort options by cost_per_tCO2e_usd ascending and compute cumulative_abatement_tCO2e in that sorted order.
                            5) Return a short narrative explaining which levers dominate and why.

                            OUTPUT:
                            - Must conform exactly to the MaccResult schema.
                            """,
            output_type=self.MaccResult,
            tools=[
                FileSearchTool(vector_store_ids=[self.academic_vector_store]),
            ],
        )

    def _build_academic_roi_agent(self) -> "Agent":
        return Agent(
            name="Academic ROI Advisor",
            model=self.agent_model,
            instructions="""
                            You analyze the provided academic MACC options.

                            TASKS:
                            - Identify the top 3 lowest-cost-per-tCO2e options (including negative/near-zero if present).
                            - Identify the top 3 highest total_effective_abatement_tCO2e options.
                            - Compare which category dominates (campus operations vs research vs workforce).
                            - Call out risks: attribution uncertainty, time-to-impact, organizational constraints.

                            PLOTTING:
                            - Plot a bar chart for cost_per_tCO2e_usd (sorted order) using plot_bar_chart.

                            REQUIREMENTS:
                            1) Return a plaintext response with three sections ONLY: findings, ranked lists (be sure to give easy-to-understand names to each item on the list), and takeaways.
                            2) Create the bar chart using plot_bar_chart with no explanation/chart note after plotting (assume the user knows where it is saved).
                            """,
            output_type=str,
            tools=[plot_bar_chart],
        )

    def _build_conversational_agent(self):
        return Agent(
            name="Academic MACC Conversational Agent",
            model=self.agent_model,
            instructions="""
                            You are the user-facing assistant for academic MACC follow-up questions.
                            Use latest_workflow_output as factual context for numbers.
                            If asked to modify assumptions (discount rate, institution type, attribution method), explain how it would change results and recommend re-running the workflow.
                            """,
            output_type=str,
        )

    #################
    # WORKFLOW RUN  #
    #################

    async def run(self, user_input: str):
        # 1) Build the MACC dataset
        macc_result = await Runner.run(self.academic_macc_agent, user_input)
        final_macc = macc_result.final_output_as(self.MaccResult)
        self.latest_workflow_output = final_macc

        # 2) ROI analysis + plot (pass the structured result)
        roi_result = await Runner.run(
            self.academic_roi_agent,
            final_macc.model_dump_json(),
        )

        return roi_result

    async def chat(self, user_input: str) -> str:
        # Optional: conversational follow-ups without rebuilding the MACC
        ctx = (
            self.latest_workflow_output.model_dump_json(indent=2)
            if self.latest_workflow_output
            else "No academic MACC has been generated yet."
        )

        result = await Runner.run(
            self.conversational_agent,
            f"latest_workflow_output:\n{ctx}\n\nuser:\n{user_input}",
        )
        return result.final_output
