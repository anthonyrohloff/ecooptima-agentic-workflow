from agents import Runner
from agents.exceptions import InputGuardrailTripwireTriggered
import asyncio
from pathlib import Path
import os
import json


# Import functions
from ecooptima_tools import _generate_timestamp
from workflows import CommunityWorkflow


############################
######### LOGGING ##########
############################


# Response logging structure
class RunLog:
    timestamp: str
    input: str
    response: str


#####################
### MAIN FUNCTION ###
#####################


async def run_community_pipeline(user_input: str) -> str:
    workflow = CommunityWorkflow()

    RunLog.timestamp = _generate_timestamp()
    log_dir = Path("response_log") / RunLog.timestamp
    log_dir.mkdir(parents=True, exist_ok=True)
    os.environ["ECOOPTIMA_LOG_DIR"] = str(log_dir)

    result = await Runner.run(workflow.plant_matrix_agent, user_input)
    result = await Runner.run(
        workflow.local_roi_agent, result.final_output.model_dump_json()
    )

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
async def main(
    user_text,
    mode: str = "analyze",
    workflow: str = "community",
    session_state: dict | None = None,
):
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
            match workflow:
                case "community":
                    response = await run_community_pipeline(user_input)
                case "consumer":
                    print("CASE STATEMENT")
                case _:
                    response = "no response (default case hit)"

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
