---
license: apache-2.0
language:
  - en
pretty_name: Five Desks tasks
tags:
  - openenv
  - reinforcement-learning
  - finance
  - science
  - math
  - security
  - media
size_categories:
  - n<1K
---

# Five Desks tasks

Procedural RL tasks in the five domains where no arena run has scored yet:
finance, natural science, math, cybersecurity, media.

Environment code: this repo (`five_desks/`). The server builds each task from
its fixed seed — the dataset lists task IDs only, not the workspaces.

## What the environment teaches

Every episode is a small virtual workspace. The agent searches with `grep`,
reads files with `read`, computes with `calc`, and finishes with `answer`
(8 steps max, short JSON observations). A deterministic verifier recomputes
the answer from the seed.

| Domain | File | Task |
| --- | --- | --- |
| finance | `ledger.csv` | One id billed twice with different amounts; report `<id>:<higher amount>` (partial credit 0.5/part) |
| science | `sensors.txt` | First sensor above threshold after the 12:20:00 calibration |
| math | `equations.txt` | First wrong equation line (use `calc` to check) |
| security | `auth.log` | First IP to reach 3 failed logins after the 12:20:00 deploy |
| media | `captions.txt` | First caption over 90 characters |

## Files

| File | Contents |
| --- | --- |
| `tasks.jsonl` | One task per line: `task_id` + `split`. All 20 tasks are `train`. |

## Reward

- `1.0`: correct answer. Finance gives `0.5` per correct part.
- `0.0`: wrong answer, `unanswered` finish, or no steps left.

## Splits

All 20 tasks are `train` (4 levels per domain: L1 easy → L3 with decoys).

## License

Apache License 2.0.
