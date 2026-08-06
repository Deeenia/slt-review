# Repository guidance

- Preserve the fixed low-cost route: active Sol plans, Luna implements, fresh read-only Terra reviews.
- Keep the normal successful path to exactly two child-agent calls.
- Do not add Terra implementation, Sol auditing, model handshakes, risk modes, hashes, manifests, or duplicate verification.
- Keep `.slt-review/boundary.md` minimal and exclude it from product results.
- Keep only `luna-worker.toml` and `terra-reviewer.toml` as installed custom agents.
- Use Sol, Luna, and Terra as user-visible names.
- Keep skill and agent instructions in English; only README files are bilingual.
- Run `python scripts/validate_repo.py` and `python -m unittest discover -s tests -v` after changes.
