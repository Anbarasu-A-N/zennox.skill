# Contributing to Zennox

Thanks for helping. Keep changes in the spirit of the skill: the least new code that solves
the problem, with no loss of safety or accessibility.

1. Fork, branch from `main`, and keep each pull request to one change.
2. Skill files live in `plugins/zennox/skills/zennox/`. Keep `SKILL.md` short (it is a router);
   put detail in `references/`.
3. Scripts must stay Python 3.10+ **standard library only** and run on Windows, macOS and Linux.
4. Add or update a test in `tests/test_scripts.py` for any script change, rebuild the package
   with `python tools/build_skill.py`, then run: `python -m unittest discover -s tests -v`
5. Describe what changed and why in the pull request, and add a line to `CHANGELOG.md`.

Security issues: please open a private security advisory on GitHub instead of a public issue.
