## Gene submission checklist (maintainers + contributors)

- [ ] One gene per PR (L0: max 5 files / 20 per creator per day)
- [ ] File is named by its SHA-256 and lives in `genes/` (L2 content-address)
- [ ] YAML header: `life_id` (`PGN@…`), `creator`, `description` ≥ 10 chars (L1/L3/L4)
- [ ] No dangerous calls (L5); `purity: pure` claims survive the sandbox check (L6)
- [ ] If signed: `signatures/<sha>.sig` attached AND creator public identity pasted in the PR
      description (maintainer: append it to `policy/trusted_keys.json` in this PR)
- [ ] `python -m pytest tests/ -q` green locally

Non-gene PRs (docs/tooling): drop what does not apply.
