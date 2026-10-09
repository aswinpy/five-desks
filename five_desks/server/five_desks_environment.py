# SPDX-License-Identifier: Apache-2.0
"""Five Desks environment: one server, five procedural domains."""

from __future__ import annotations

import ast
import operator
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

from five_desks.generators import TASKS, build_task
from five_desks.models import FiveDesksAction, FiveDesksObservation

MAX_STEPS = 8
MAX_MATCHES = 8
MAX_OUTPUT_CHARS = 1200

_episode: dict | None = None

_ALLOWED_BINOPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
                   ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod}
_ALLOWED_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def safe_calc(expr: str) -> float:
    """Evaluate digits + +-*/() and spaces only. Raises ValueError otherwise."""
    if len(expr) > 200 or not expr.strip():
        raise ValueError("empty or too long")
    tree = ast.parse(expr, mode="eval")
    for node in ast.walk(tree):
        if isinstance(node, ast.Expression):
            continue
        if isinstance(node, ast.Constant):
            if not isinstance(node.value, (int, float)):
                raise ValueError("numbers only")
            continue
        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
            continue
        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY:
            continue
        if isinstance(node, (ast.Load, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.UAdd, ast.USub)):
            continue
        raise ValueError("only +-*/() on numbers")

    def _eval(n):
        if isinstance(n, ast.Expression):
            return _eval(n.body)
        if isinstance(n, ast.Constant):
            return n.value
        if isinstance(n, ast.BinOp):
            return _ALLOWED_BINOPS[type(n.op)](_eval(n.left), _eval(n.right))
        if isinstance(n, ast.UnaryOp):
            return _ALLOWED_UNARY[type(n.op)](_eval(n.operand))
        raise ValueError("bad node")

    return _eval(tree)


class FiveDesksEnvironment(Environment):
    """Grep / read / calc workspace, then answer. Deterministic verifier."""

    SUPPORTS_CONCURRENT_SESSIONS: bool = False

    def reset(self, seed=None, episode_id=None, task_id=None, **kwargs) -> FiveDesksObservation:
        global _episode
        task_id = task_id or next(iter(TASKS))
        if task_id not in TASKS:
            raise ValueError(f"unknown task_id {task_id!r}")
        domain, files, question, answer, verify = build_task(task_id)
        _episode = {
            "episode_id": episode_id or str(uuid4()),
            "task_id": task_id,
            "domain": domain,
            "files": files,
            "answer": answer,
            "verify": verify,
            "steps": 0,
            "done": False,
            "reward": 0.0,
        }
        return self._obs(question=question, files=", ".join(sorted(files)), output="", done=False, reward=0.0, first=True)

    def step(self, action: FiveDesksAction, timeout_s=None, **kwargs) -> FiveDesksObservation:
        ep = self._req()
        if ep["done"]:
            return self._obs(output="the episode is over", done=True, reward=ep["reward"])
        ep["steps"] += 1
        fields = [action.grep is not None, action.read is not None, action.calc is not None, action.answer is not None]
        if sum(fields) != 1:
            out = "send exactly one of grep, read, calc, or answer"
            return self._cont(out)
        if action.answer is not None:
            reward = float(ep["verify"](action.answer))
            reward = max(0.0, min(1.0, reward))
            label = "correct" if reward >= 1.0 else ("partial" if reward > 0 else "wrong")
            return self._finish(reward, label)
        if action.grep is not None:
            needle = action.grep.lower()
            corpus: list[str] = []
            for fname, text in ep["files"].items():
                for line in text.splitlines():
                    corpus.append(f"{fname}: {line}")
            matches = [l for l in corpus if needle in l.lower()] if needle else corpus[:MAX_MATCHES]
            if not needle:
                matches = corpus[:MAX_MATCHES]
            out = "\n".join(matches[:MAX_MATCHES]) or "no matching lines"
            if len(matches) > MAX_MATCHES:
                out += f"\n({len(matches)} matches, first {MAX_MATCHES} shown)"
            return self._cont(out[:MAX_OUTPUT_CHARS])
        if action.read is not None:
            fname = action.read.strip()
            if fname not in ep["files"]:
                return self._cont(f"unknown file. files: {', '.join(sorted(ep['files']))}")
            lines = ep["files"][fname].splitlines()[:40]
            return self._cont("\n".join(lines)[:MAX_OUTPUT_CHARS])
        # calc
        try:
            val = safe_calc(action.calc)
            if isinstance(val, float) and val.is_integer():
                val = int(val)
            return self._cont(f"= {val}")
        except Exception as e:
            return self._cont(f"calc error: {e}")

    @property
    def state(self) -> State:
        ep = _episode or {}
        return State(episode_id=ep.get("episode_id"), step_count=ep.get("steps", 0))

    def _req(self) -> dict:
        if _episode is None:
            raise RuntimeError("call reset() before step()")
        return _episode

    def _cont(self, output: str) -> FiveDesksObservation:
        ep = self._req()
        if ep["steps"] >= MAX_STEPS:
            return self._finish(0.0, output + "\nno steps left")
        return self._obs(output=output, done=False, reward=0.0)

    def _finish(self, reward: float, output: str) -> FiveDesksObservation:
        ep = self._req()
        ep["done"] = True
        ep["reward"] = reward
        return self._obs(output=output, done=True, reward=reward)

    def _obs(self, output: str, done: bool, reward: float, question: str = "", files: str = "", first: bool = False) -> FiveDesksObservation:
        ep = self._req()
        return FiveDesksObservation(
            task_id=ep["task_id"],
            domain=ep["domain"],
            question=question if (first or ep["steps"] == 0) else "",
            files=files if first else "",
            output=output,
            steps_left=max(0, MAX_STEPS - ep["steps"]),
            done=done,
            reward=reward,
        )
