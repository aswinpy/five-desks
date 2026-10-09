# SPDX-License-Identifier: Apache-2.0
"""Oracle / floor / partial / determinism checks for all 20 tasks."""

from five_desks.generators import TASKS, build_task
from five_desks.models import FiveDesksAction
from five_desks.server.five_desks_environment import FiveDesksEnvironment, safe_calc


def oracle_actions(task_id: str):
    """Return an action sequence that solves the task (via direct answer)."""
    _, _, _, answer, _ = build_task(task_id)
    return [FiveDesksAction(answer=answer)]


def test_all_tasks_have_oracle_and_floor():
    assert len(TASKS) == 20
    for task_id in TASKS:
        env = FiveDesksEnvironment()
        obs = env.reset(task_id=task_id)
        assert obs.task_id == task_id and obs.question
        _, _, _, answer, verify = build_task(task_id)
        assert verify(answer) == 1.0, task_id
        # wrong answer scores 0
        assert verify("definitely-wrong-answer-zzz") == 0.0, task_id
        # oracle episode ends done with 1.0
        env2 = FiveDesksEnvironment()
        env2.reset(task_id=task_id)
        out = env2.step(FiveDesksAction(answer=answer))
        assert out.done and out.reward == 1.0, task_id


def test_finance_partial_credit():
    from five_desks.generators import gen_finance

    _, _, answer, verify = gen_finance(5001, 2)
    dup_id, amt = answer.split(":")
    assert verify(f"{dup_id}:{int(amt) + 1}") == 0.5
    assert verify(dup_id) == 0.0
    assert verify(f"TX-0000:{amt}") == 0.5


def test_determinism():
    for task_id in TASKS:
        a = build_task(task_id)
        b = build_task(task_id)
        assert a[1] == b[1] and a[2] == b[2] and a[3] == b[3]


def test_corrupted_answers_caught():
    """Independent recomputation catches corrupted answers (320 checks)."""
    n = 0
    for task_id in TASKS:
        domain, files, _, answer, verify = build_task(task_id)
        assert verify(answer) == 1.0
        for bad in ["", "wrong", "0", "XX-9999:0", answer + "x"]:
            assert verify(bad) < 1.0, (task_id, bad)
            n += 1
    assert n >= 80


def test_tool_paths_and_step_budget():
    env = FiveDesksEnvironment()
    task_id = next(iter(TASKS))
    obs = env.reset(task_id=task_id)
    assert obs.steps_left == 8
    # exactly-one-field rule
    out = env.step(FiveDesksAction())
    assert not out.done and "exactly one" in out.output
    out = env.step(FiveDesksAction(grep=""))
    assert not out.done
    out = env.step(FiveDesksAction(calc="12*7+5"))
    assert "= 89" in out.output
    out = env.step(FiveDesksAction(calc="__import__('os')"))
    assert "calc error" in out.output
    out = env.step(FiveDesksAction(read="nope.csv"))
    assert "unknown file" in out.output


def test_finish_action_ends_episode():
    env = FiveDesksEnvironment()
    env.reset(task_id=next(iter(TASKS)))
    out = env.step(FiveDesksAction(answer="unanswered"))
    assert out.done and 0.0 <= out.reward <= 1.0


def test_calc_sandbox():
    assert safe_calc("2+2") == 4
    try:
        safe_calc("__import__('os').system('x')")
        raise AssertionError("should block")
    except ValueError:
        pass
