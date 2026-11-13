# Notes for AI coding agents

This is the Home Assistant integration for MadPlan. MadPlan itself is a Home Assistant app in
[olenoerby/ha-madplan-app](https://github.com/olenoerby/ha-madplan-app): its API under `/api/v1/ha`
and the rules that govern it live there, so read its `docs/AI_CONTEXT.md` first. The integration
reaches the app at `http://<app hostname>:8099` with a personal token, never through ingress.

- Entity ids are fixed, as `sensor.madplan_*`, whatever the language or household name, so that
  dashboards and automations can be copied as they are. Do not change an existing one.
- Services only do what a person would do with a button in MadPlan. Nothing here should send a plan
  to Mealie or change anything by itself.
- A change that needs a new field or route in the app goes into ha-madplan-app first, and the
  README here says which app version it needs.
- `hassfest` and the HACS validation in `.github/workflows/validate.yml` must pass.
- Documentation, READMEs, comments and commit messages are in English. What people see in Home
  Assistant comes in English and Danish: `strings.json`, `translations/en.json` and
  `translations/da.json` must all have every key.
