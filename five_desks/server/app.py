# SPDX-License-Identifier: Apache-2.0
"""HTTP + WebSocket server for Five Desks."""

from openenv.core.env_server.http_server import create_app

from five_desks.models import FiveDesksAction, FiveDesksObservation
from five_desks.server.five_desks_environment import FiveDesksEnvironment

app = create_app(
    FiveDesksEnvironment,
    FiveDesksAction,
    FiveDesksObservation,
    env_name="five_desks",
    max_concurrent_envs=1,
)


def main(host: str = "0.0.0.0", port: int = 8000) -> None:
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
