# SPDX-License-Identifier: Apache-2.0
"""Deterministic procedural generators + verifiers for the five zero-domains."""

from __future__ import annotations

import random

DEPLOY_CLOCK = "12:20:00"
DEPLOY_S = 12 * 3600 + 20 * 60


def _clock(s: int) -> str:
    h, r = divmod(s, 3600)
    m, sec = divmod(r, 60)
    return f"{h:02d}:{m:02d}:{sec:02d}"


# ---------------- finance: duplicate id, two amounts ----------------

FIN_ACCOUNTS = ["ops", "travel", "ads", "infra", "support", "sales"]


def gen_finance(seed: int, level: int = 1):
    rng = random.Random(seed)
    n = {1: 12, 2: 14, 3: 18}[level]
    dup_id = f"TX-{rng.randint(1000, 9999)}"
    amt1 = rng.randint(20, 900)
    delta = rng.randint(1, 60)
    amt2 = amt1 + delta  # higher second amount
    # decoy id appearing twice with same amount (legit, ignored)
    decoy_ids = []
    if level >= 2:
        for _ in range(level - 1):
            decoy_ids.append(f"TX-{rng.randint(1000, 9999)}")
    ids_used = {dup_id} | set(decoy_ids)
    lines = []
    # first occurrence of dup
    lines.append(f"{dup_id},{rng.choice(FIN_ACCOUNTS)},{amt1}")
    for _ in range(n - 2 - 2 * len(decoy_ids)):
        tx = f"TX-{rng.randint(1000, 9999)}"
        while tx in ids_used:
            tx = f"TX-{rng.randint(1000, 9999)}"
        ids_used.add(tx)
        lines.append(f"{tx},{rng.choice(FIN_ACCOUNTS)},{rng.randint(20, 900)}")
    for d in decoy_ids:
        a = rng.randint(20, 900)
        lines.append(f"{d},{rng.choice(FIN_ACCOUNTS)},{a}")
        lines.append(f"{d},{rng.choice(FIN_ACCOUNTS)},{a}")
    rng.shuffle(lines)
    # ensure second dup occurrence is not adjacent (needs search)
    lines.append(f"{dup_id},{rng.choice(FIN_ACCOUNTS)},{amt2}")
    rng.shuffle(lines)
    header = "id,account,amount"
    text = header + "\n" + "\n".join(lines)
    question = (
        "One transaction id appears twice with DIFFERENT amounts (a double bill). "
        f"Report it and the HIGHER amount as '<id>:<amount>'. Files: ledger.csv. "
        'Use {"grep": "<text>"} / {"read": "ledger.csv"} / {"calc": "2+2"}. '
        'Finish with {"answer": "TX-1234:567"}.'
    )
    answer = f"{dup_id}:{amt2}"

    def verify(ans: str) -> float:
        parts = ans.strip().split(":")
        if len(parts) != 2:
            return 0.0
        got_id = parts[0].strip().upper()
        try:
            got_amt = int(parts[1].strip())
        except ValueError:
            try:
                got_amt = int(float(parts[1].strip()))
            except ValueError:
                return 0.5 if got_id == dup_id else 0.0
        s = 0.0
        if got_id == dup_id:
            s += 0.5
        if got_amt == amt2:
            s += 0.5
        return s

    return {"ledger.csv": text}, question, answer, verify


# ---------------- science: first sensor over threshold after event ----------------

SENSORS = ["T1", "T2", "T3", "T4", "P1", "P2"]


def gen_science(seed: int, level: int = 1):
    rng = random.Random(seed)
    threshold = rng.choice([70.0, 75.0, 80.0])
    n = {1: 28, 2: 34, 3: 40}[level]
    used = set()
    events: list[tuple[int, str, float]] = []
    # decoy pre-event exceedances
    for _ in range(rng.randint(1, 2)):
        t = rng.randrange(12 * 3600, DEPLOY_S)
        while t in used:
            t = rng.randrange(12 * 3600, DEPLOY_S)
        used.add(t)
        events.append((t, rng.choice(SENSORS), round(threshold + rng.uniform(1, 10), 1)))
    for _ in range(n):
        t = rng.randrange(12 * 3600, 13 * 3600)
        while t in used:
            t = rng.randrange(12 * 3600, 13 * 3600)
        used.add(t)
        # mostly below threshold
        v = round(rng.uniform(threshold - 25, threshold - 1), 1)
        events.append((t, rng.choice(SENSORS), v))
    # 2-3 true post-event exceedances
    n_true = rng.randint(2, 3)
    true_events = []
    for _ in range(n_true):
        t = rng.randrange(DEPLOY_S + 1, 13 * 3600)
        while t in used:
            t = rng.randrange(DEPLOY_S + 1, 13 * 3600)
        used.add(t)
        s = rng.choice(SENSORS)
        v = round(threshold + rng.uniform(1, 12), 1)
        true_events.append((t, s, v))
        events.append((t, s, v))
    events.sort()
    lines = [f"{_clock(t)} sensor={s} value={v}" for t, s, v in events]
    lines.append(f"{DEPLOY_CLOCK} calibration event=deploy")
    lines.sort()
    first = min(true_events)
    answer = first[1]
    question = (
        f"After the {DEPLOY_CLOCK} calibration, which sensor FIRST read above {threshold}? "
        "Files: sensors.txt. "
        'Use {"grep": "<text>"} / {"read": "sensors.txt"}. '
        'Finish with {"answer": "<sensor>"} e.g. {"answer": "T3"}.'
    )

    def verify(ans: str) -> float:
        return 1.0 if ans.strip().upper() == answer else 0.0

    return {"sensors.txt": "\n".join(lines)}, question, answer, verify


# ---------------- math: first wrong equation ----------------

def _rand_expr(rng: random.Random, level: int):
    a = rng.randint(6, 49 if level < 3 else 99)
    b = rng.randint(6, 49 if level < 3 else 99)
    c = rng.randint(2, 12)
    kind = rng.choice(["add_mul", "paren", "sub_div"] if level >= 2 else ["add_mul"])
    if kind == "add_mul":
        val = a * b + c
        expr = f"{a}*{b}+{c}"
    elif kind == "paren":
        val = (a + b) * c if rng.random() < 0.5 else a * (b + c)
        expr = f"({a}+{b})*{c}" if val == (a + b) * c else f"{a}*({b}+{c})"
    else:
        base = a * c
        val = base - b
        expr = f"{a}*{c}-{b}"
    return expr, val


def gen_math(seed: int, level: int = 1):
    rng = random.Random(seed)
    n = {1: 6, 2: 8, 3: 10}[level]
    wrong_idx = rng.randrange(n)
    lines = []
    for i in range(n):
        expr, val = _rand_expr(rng, level)
        if i == wrong_idx:
            off = rng.choice([-2, -1, 1, 2, 10] if level >= 2 else [1, 2, -1])
            shown = val + off
        else:
            shown = val
        lines.append(f"{i + 1}: {expr} = {shown}")
    answer = str(wrong_idx + 1)
    question = (
        "The equations list has exactly ONE wrong result. Which line number is wrong? "
        "Files: equations.txt. "
        'Use {"read": "equations.txt"} and {"calc": "12*7+5"}. '
        'Finish with {"answer": "<line>"} e.g. {"answer": "4"}.'
    )

    def verify(ans: str) -> float:
        return 1.0 if ans.strip() == answer else 0.0

    return {"equations.txt": "\n".join(lines)}, question, answer, verify


# ---------------- security: first IP with >=3 fails after deploy ----------------

def _rand_ip(rng: random.Random) -> str:
    return f"10.{rng.randint(0, 3)}.{rng.randint(0, 9)}.{rng.randint(2, 250)}"


def gen_security(seed: int, level: int = 1):
    rng = random.Random(seed)
    k = 3
    n_noise = {1: 24, 2: 30, 3: 38}[level]
    attacker = _rand_ip(rng)
    others = [_rand_ip(rng) for _ in range(6)]
    used = set()
    events: list[tuple[int, str, str]] = []  # t, ip, status

    def pick(low, high):
        while True:
            t = rng.randrange(low, high)
            if t not in used:
                used.add(t)
                return t

    # pre-deploy decoy brute force (does not count)
    decoy = rng.choice(others)
    for _ in range(3):
        events.append((pick(12 * 3600, DEPLOY_S), decoy, "FAIL"))
    for _ in range(n_noise):
        events.append((pick(12 * 3600, 13 * 3600), rng.choice(others), rng.choice(["FAIL", "OK", "OK", "OK"])))
    # attacker fails after deploy
    atk_times = sorted(pick(DEPLOY_S + 1, 13 * 3600) for _ in range(k + rng.randint(0, 2)))
    for t in atk_times:
        events.append((t, attacker, "FAIL"))
    # decoy with only 2 fails after deploy
    decoy2 = rng.choice([o for o in others if o != decoy])
    for _ in range(2):
        events.append((pick(DEPLOY_S + 1, 13 * 3600), decoy2, "FAIL"))
    events.sort()
    lines = [f"{_clock(t)} ip={ip} status={st} user=u{rng.randint(1, 9)}" for t, ip, st in events]
    lines.append(f"{DEPLOY_CLOCK} deploy service=auth")
    lines.sort()
    answer = attacker
    question = (
        f"After the {DEPLOY_CLOCK} deploy, which IP FIRST reached {k} failed logins? "
        "Files: auth.log. "
        'Use {"grep": "<ip or FAIL>"} / {"read": "auth.log"}. '
        'Finish with {"answer": "<ip>"} e.g. {"answer": "10.0.1.7"}.'
    )

    def verify(ans: str) -> float:
        return 1.0 if ans.strip() == answer else 0.0

    return {"auth.log": "\n".join(lines)}, question, answer, verify


# ---------------- media: first caption over 90 chars ----------------

MEDIA_WORDS = ["harbor", "festival", "market", "bridge", "orchestra", "garden", "parade", "lighthouse", "tram", "bakery", "mural", "comet"]


def _rand_caption(rng: random.Random, long: bool) -> str:
    n = rng.randint(14, 22) if long else rng.randint(6, 13)
    words = [rng.choice(MEDIA_WORDS) for _ in range(n)]
    s = "A " + " ".join(words) + "."
    s = s[0].upper() + s[1:]
    if not long and len(s) > 90:
        return s[:88] + "."
    if long and len(s) <= 90:
        s += " Crowds gather along the promenade at dusk."
    return s


def gen_media(seed: int, level: int = 1):
    rng = random.Random(seed)
    n = {1: 7, 2: 9, 3: 12}[level]
    first_long = rng.randrange(n)
    lines = []
    for i in range(n):
        # decoys near 85-89 chars before the answer
        if i < first_long and level >= 2 and rng.random() < 0.4:
            cap = _rand_caption(rng, False)
            while len(cap) < 80:
                cap = _rand_caption(rng, False)
        elif i == first_long:
            cap = _rand_caption(rng, True)
        else:
            cap = _rand_caption(rng, rng.random() < 0.25 and i > first_long)
            if i < first_long and len(cap) > 90:
                cap = _rand_caption(rng, False)
        lines.append(f"{i + 1}: {cap}")
    answer = str(first_long + 1)
    question = (
        "Captions over 90 characters break the layout. Which line number is the FIRST one over 90 chars? "
        "Files: captions.txt. "
        'Use {"read": "captions.txt"}. '
        'Finish with {"answer": "<line>"} e.g. {"answer": "5"}.'
    )

    def verify(ans: str) -> float:
        return 1.0 if ans.strip() == answer else 0.0

    return {"captions.txt": "\n".join(lines)}, question, answer, verify


GENERATORS = {
    "finance": gen_finance,
    "science": gen_science,
    "math": gen_math,
    "security": gen_security,
    "media": gen_media,
}

# task_id -> (domain, seed, level)
TASKS: dict[str, tuple[str, int, int]] = {}
_specs = [
    ("finance", 5000, 1), ("finance", 5001, 2), ("finance", 5002, 2), ("finance", 5003, 3),
    ("science", 5100, 1), ("science", 5101, 2), ("science", 5102, 2), ("science", 5103, 3),
    ("math", 5200, 1), ("math", 5201, 2), ("math", 5202, 2), ("math", 5203, 3),
    ("security", 5300, 1), ("security", 5301, 2), ("security", 5302, 2), ("security", 5303, 3),
    ("media", 5400, 1), ("media", 5401, 2), ("media", 5402, 2), ("media", 5403, 3),
]
for i, (_domain, _seed, _level) in enumerate(_specs):
    TASKS[f"{_domain}-{i % 4:02d}"] = (_domain, _seed, _level)


def build_task(task_id: str):
    domain, seed, level = TASKS[task_id]
    files, question, answer, verify = GENERATORS[domain](seed, level)
    return domain, files, question, answer, verify
