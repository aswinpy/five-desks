# SPDX-License-Identifier: Apache-2.0
"""Typed client for Five Desks."""

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from five_desks.models import FiveDesksAction, FiveDesksObservation


class FiveDesksEnv(EnvClient[FiveDesksAction, FiveDesksObservation, State]):
    """Client for the Five Desks environment."""

    def _step_payload(self, action: FiveDesksAction) -> dict:
        return action.model_dump(exclude_none=True)

    def _parse_result(self, payload: dict) -> StepResult[FiveDesksObservation]:
        obs_data = payload.get("observation", {})
        observation = FiveDesksObservation(
            task_id=obs_data.get("task_id", ""),
            domain=obs_data.get("domain", ""),
            question=obs_data.get("question", ""),
            files=obs_data.get("files", ""),
            output=obs_data.get("output", ""),
            steps_left=obs_data.get("steps_left", 0),
            done=payload.get("done", False),
            reward=payload.get("reward"),
            metadata=payload.get("metadata", obs_data.get("metadata", {})),
        )
        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
            metadata=payload.get("metadata"),
        )

    def _parse_state(self, payload: dict) -> State:
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )
