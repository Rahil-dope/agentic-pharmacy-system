"""
Core agent entrypoint for the Agentic AI Pharmacy Assistant System.

This module implements:
- LLM-based agent using OpenAI function calling
- Tool definitions for backend interaction (via `tools.py`)
- Agent execution loop that can perform multiple tool calls
- Minimal CLI interface for manual testing
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from openai import OpenAI

from config import MODEL_NAME, OPENAI_API_KEY
from observability import (
    create_span,
    create_trace,
    end_trace,
    flush_traces,
    log_generation,
    log_tool_call,
)
from tools import (
    check_medicine_availability,
    create_order,
    get_customer_history,
    get_refill_alerts,
)


def get_client() -> OpenAI:
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Please configure it in the .env file "
            "before running the agent.",
        )
    return OpenAI()


SYSTEM_PROMPT_TEMPLATE = (
    "You are an expert licensed pharmacist assistant for an AI-powered pharmacy. "
    "You must ALWAYS use the available tools to check medicine availability, "
    "stock, and prescription requirements before making any final decision. "
    "Never hallucinate medicine availability or stock levels.\n\n"
    "Current customer id: {customer_id}.\n\n"
    "Your responsibilities:\n"
    "1. Understand messy natural language requests about medicines and orders.\n"
    "2. Extract the medicine name and quantity from the user's input.\n"
    "3. Use the check_medicine_availability tool to verify availability.\n"
    "4. If the medicine is available and does not require a prescription, "
    "   use create_order with the current customer id to place an order.\n"
    "5. If the medicine requires a prescription, you may still create an order, "
    "   but it will be pending until verification.\n"
    "6. If the user asks about their past orders, use get_customer_history.\n"
    "7. If the user asks whether they need any refills or is running out of medicine, "
    "   use get_refill_alerts with the current customer id to check for predicted refills.\n"
    "8. Never approve or reject an order without consulting tools.\n\n"
    "When you are ready to answer the user, respond with a single JSON object only, "
    "without any extra text. The JSON must contain at least these keys:\n"
    "- message: human readable explanation for the user\n"
    "- status: one of 'approved', 'pending', 'rejected', 'refill_suggested', 'ok', or 'error'\n"
    "- order_id: include this key with the numeric id when an order is created, "
    "  otherwise you may omit it or set it to null.\n\n"
    "Examples of valid responses (do not quote or wrap them in text):\n"
    "{ \"message\": \"Your order for 5 Paracetamol has been approved.\", "
    "\"order_id\": 12, \"status\": \"approved\" }\n"
    "{ \"message\": \"Paracetamol is currently out of stock.\", \"status\": \"rejected\" }\n"
    "{ \"message\": \"This medicine requires a prescription. Your order is pending verification.\", "
    "\"order_id\": 12, \"status\": \"pending\" }\n"
    "{ \"message\": \"You are due for a refill of Paracetamol. Would you like to place an order?\", "
    "\"status\": \"refill_suggested\", \"refill_items\": [\"Paracetamol\"] }\n"
    "{ \"message\": \"You are not due for any refills at this time.\", \"status\": \"ok\" }\n\n"
    "If the backend is unavailable or a tool fails, clearly explain this in the "
    "message field and set status to 'rejected' or 'error' as appropriate."
)


TOOLS_SPEC: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "check_medicine_availability",
            "description": "Check if a given medicine is in stock and whether it requires a prescription.",
            "parameters": {
                "type": "object",
                "properties": {
                    "medicine_name": {
                        "type": "string",
                        "description": "The exact name of the medicine to check.",
                    },
                },
                "required": ["medicine_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_order",
            "description": "Create an order in the backend for a specific customer, medicine, and quantity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "integer",
                        "description": "The numeric id of the customer placing the order.",
                    },
                    "medicine_name": {
                        "type": "string",
                        "description": "The exact name of the medicine being ordered.",
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "The quantity of medicine units requested.",
                        "minimum": 1,
                    },
                },
                "required": ["customer_id", "medicine_name", "quantity"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_customer_history",
            "description": "Retrieve the order history for a specific customer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "integer",
                        "description": "The numeric id of the customer.",
                    },
                },
                "required": ["customer_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_refill_alerts",
            "description": "Retrieve predicted refill alerts for a specific customer based on order history.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "integer",
                        "description": "The numeric id of the customer.",
                    },
                },
                "required": ["customer_id"],
            },
        },
    },
]


TOOL_DISPATCH = {
    "check_medicine_availability": check_medicine_availability,
    "create_order": create_order,
    "get_customer_history": get_customer_history,
    "get_refill_alerts": get_refill_alerts,
}


def _call_llm(messages: List[Dict[str, Any]], trace: Any | None = None) -> Dict[str, Any]:
    """
    Call the LLM and, if tracing is enabled, record the generation in Langfuse.
    """
    client = get_client()

    if trace is None:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=TOOLS_SPEC,
            tool_choice="auto",
        )
        return completion.model_dump()

    # When tracing is enabled, wrap the LLM call in a Langfuse generation span.
    with create_span(trace, "llm-generation", as_type="generation", model=MODEL_NAME) as generation:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=TOOLS_SPEC,
            tool_choice="auto",
        )
        completion_dict = completion.model_dump()
        log_generation(generation, messages, completion_dict, MODEL_NAME)
        return completion_dict


def run_agent(user_input: str, customer_id: int, max_steps: int = 5) -> tuple[Dict[str, Any], str | None]:
    """
    Run the agent for a single user input and customer id.

    The agent may perform multiple tool calls before returning a final JSON-like
    response dictionary suitable for presenting to the user.

    Returns a tuple of (result_dict, trace_url_or_none).
    """
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(customer_id=customer_id)

    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]

    result: Dict[str, Any]
    trace_url: str | None = None

    with create_trace(customer_id, user_input) as trace:
        try:
            for _ in range(max_steps):
                response = _call_llm(messages, trace=trace)
                choice = response["choices"][0]["message"]

                tool_calls = choice.get("tool_calls") or []
                if tool_calls:
                    # Record the assistant message that requested tool calls.
                    messages.append(
                        {
                            "role": "assistant",
                            "content": choice.get("content"),
                            "tool_calls": tool_calls,
                        }
                    )

                    # Execute each tool call and append its result.
                    for tool_call in tool_calls:
                        func_name = tool_call["function"]["name"]
                        raw_args = tool_call["function"].get("arguments") or "{}"
                        try:
                            args = json.loads(raw_args)
                        except json.JSONDecodeError:
                            args = {}

                        tool_fn = TOOL_DISPATCH.get(func_name)
                        if not tool_fn:
                            tool_result: Dict[str, Any] = {
                                "error": f"Unknown tool: {func_name}",
                            }
                        else:
                            try:
                                tool_result = tool_fn(**args)
                            except TypeError:
                                # Argument mismatch or bad schema.
                                tool_result = {
                                    "error": f"Invalid arguments for tool {func_name}",
                                }
                            except Exception as exc:  # noqa: BLE001
                                tool_result = {
                                    "error": f"Tool {func_name} raised an exception: {exc}",
                                }

                        # Log each tool call in Langfuse.
                        log_tool_call(trace, func_name, args, tool_result)

                        # Additionally log a synthetic warehouse_webhook span when an order is created
                        # and would trigger downstream automation in the backend.
                        if (
                            func_name == "create_order"
                            and isinstance(tool_result, dict)
                            and tool_result.get("order_id") is not None
                            and tool_result.get("status") in {"approved", "pending"}
                        ):
                            log_tool_call(
                                trace,
                                "warehouse_webhook",
                                {"order_id": tool_result.get("order_id")},
                                {"status": tool_result.get("status")},
                            )

                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.get("id"),
                                "name": func_name,
                                "content": json.dumps(tool_result),
                            }
                        )

                    # Continue the loop so the model can use the tool results.
                    continue

                # No further tool calls: this should be the final answer.
                content = choice.get("content") or ""
                try:
                    parsed = json.loads(content)
                    if isinstance(parsed, dict):
                        result = parsed
                    else:
                        result = {"message": content, "status": "unknown"}
                except json.JSONDecodeError:
                    # Fallback: wrap free-form text into a structured response.
                    result = {"message": content, "status": "unknown"}

                meta = end_trace(trace, result)
                trace_url = meta.get("trace_url")
                return result, trace_url

            # Safety fallback if the loop ends without a final answer.
            result = {
                "message": "The agent could not complete the request within the step limit.",
                "status": "error",
            }
            meta = end_trace(trace, result)
            trace_url = meta.get("trace_url")
            return result, trace_url
        except Exception as exc:  # noqa: BLE001
            # Ensure the trace is still closed and the error is visible in Langfuse.
            result = {
                "message": f"Unexpected error in agent: {exc}",
                "status": "error",
            }
            meta = end_trace(trace, result, error=exc)
            trace_url = meta.get("trace_url")
            return result, trace_url


def _cli_loop() -> None:
    print("Agentic AI Pharmacy Assistant CLI")
    print("Backend must be running at http://localhost:8000")
    print("Press Ctrl+C to exit.\n")

    while True:
        try:
            raw_customer_id = input("Enter customer id: ").strip()
            if not raw_customer_id:
                print("Customer id is required.")
                continue
            try:
                customer_id = int(raw_customer_id)
            except ValueError:
                print("Customer id must be an integer.")
                continue

            while True:
                user_text = input("You: ").strip()
                if not user_text:
                    print("Empty input, please type a request or press Ctrl+C to exit.")
                    continue

                try:
                    result, trace_url = run_agent(user_text, customer_id)
                except RuntimeError as exc:
                    print(f"Agent error: {exc}")
                    return
                except Exception as exc:  # noqa: BLE001
                    print(f"Unexpected error while running agent: {exc}")
                    continue

                print("Agent:", json.dumps(result, indent=2))
                if trace_url:
                    print(f"\nTrace URL: {trace_url}")

                # Flush telemetry for interactive CLI usage.
                flush_traces()

        except KeyboardInterrupt:
            print("\nExiting agent CLI.")
            break


if __name__ == "__main__":
    _cli_loop()

