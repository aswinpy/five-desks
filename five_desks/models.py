# SPDX-License-Identifier: Apache-2.0
"""Actions and observations for Five Desks."""

from openenv.core.env_server.types import Action, Observation
from pydantic import Field


class FiveDesksAction(Action):
    """Search, read, compute, or answer. Send exactly one field per turn."""

    grep: str | None = Field(
        default=None,
        max_length=200,
        description="Return up to 8 workspace lines containing this text (case-insensitive). Empty string returns first 8 lines.",
    )
    read: str | None = Field(
        default=None,
        max_length=64,
        description="Read a workspace file by name (e.g. 'ledger.csv'). Returns first 40 lines.",
    )
    calc: str | None = Field(
        default=None,
        max_length=200,
        description="Evaluate a bounded arithmetic expression (digits, +-*/() and spaces only, max 200 chars).",
    )
    answer: str | None = Field(
        default=None,
        max_length=128,
        description="Submit the final answer. Ends the episode.",
    )


class FiveDesksObservation(Observation):
    """What the agent sees after each action."""

    task_id: str = Field(default="", description="Task being played")
    domain: str = Field(default="", description="One of finance, science, math, security, media")
    question: str = Field(default="", description="The question. Sent once, at reset.")
    files: str = Field(default="", description="Workspace file names. Sent once, at reset.")
    output: str = Field(default="", description="Result of the last action")
    steps_left: int = Field(default=0, description="Actions left before the episode ends")
