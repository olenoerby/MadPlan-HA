# MadPlan integration for Home Assistant

<img src="custom_components/madplan_app/brand/logo.png" alt="MadPlan" width="320">

The Home Assistant **integration** for MadPlan, a meal planner for Danish households built around
current supermarket offers. It shows the meal plan, the shopping list, the pantry and the budget as
entities in Home Assistant, for dashboards and automations, and lets people vote on meals, say what
was made and send the plan to Mealie from their phone.

It is not MadPlan itself. MadPlan is a Home Assistant **app** (formerly an add-on), in
[olenoerby/ha-madplan-app](https://github.com/olenoerby/ha-madplan-app), installed under
Settings → Apps. This integration is optional, runs beside the app, and only talks to it with a
personal token. The stand-alone MadPlan server it was first made for is no longer maintained.

From Home Assistant 2026.3 it shows MadPlan's own icon and logo, from `custom_components/madplan_app/brand/`.

## Install

1. Install and set up the MadPlan app first, from
   [olenoerby/ha-madplan-app](https://github.com/olenoerby/ha-madplan-app).
2. In MadPlan: **Settings → Home Assistant → Create token** ("Opret token" in Danish). Copy it, as it
   is only shown once. The integration acts as the person who made the token.
3. In HACS, open the menu → **Custom repositories**, add
   `https://github.com/olenoerby/ha-madplan-integration` with the type **Integration**, then download
   **MadPlan** and restart Home Assistant.
4. In Home Assistant: **Settings → Devices & services → Add integration → MadPlan**. Enter the token
   and the app's address inside Home Assistant: `http://<hostname>:8099`, where the hostname is on
   the MadPlan app's **Info** tab, such as `88efefb2-madplan`. Home Assistant reaches the app
   directly, so no port has to be opened.

To appear in the HACS store without the custom-repository step, the repository must be public, have
a GitHub release, pass the `HACS validation` and `hassfest` checks in `.github/workflows/validate.yml`, and be
submitted to [hacs/default](https://github.com/hacs/default). Icons shown in the store need a
submission to [home-assistant/brands](https://github.com/home-assistant/brands). Those are steps
for the repository owner.

### Upgrading from 0.4

From 0.5.0 the integration's domain is `madplan_app`, not `madplan`, as another, unrelated
integration also used `madplan`, and the two could overwrite each other or be mistaken for each
other, icons included. The entities keep their ids, such as `sensor.madplan_dinner_today`, so
dashboards and automations that use them work as before. Services are now called as
`madplan_app.send_to_mealie` and so on.

1. Update in HACS and restart Home Assistant.
2. Delete the old MadPlan entry under **Settings → Devices & services**, then add MadPlan again
   with the same address and token.
3. Change automations that call `madplan.<service>` to `madplan_app.<service>`.
4. If a folder `custom_components/madplan` is left behind, delete it and restart.

## What you get

| Entity | Shows |
|---|---|
| `calendar.madplan_meal_plan` | The meal plan |
| `todo.madplan_shopping_list` | The shopping list. Ticking something off here ticks it off in MadPlan |
| `sensor.madplan_dinner_today` | Today's dinner, with all of the day's meals as an attribute |
| `sensor.madplan_next_meal` | The next meal |
| `sensor.madplan_meals_to_vote` | Meals you have not answered yet, with their ids in the `meals` attribute |
| `sensor.madplan_meals_not_sent` | Accepted meals Mealie does not have yet, listed in the `meals` attribute |
| `sensor.madplan_shopping_remaining` and `sensor.madplan_shopping_cost` | Status of the shopping list |
| `sensor.madplan_expiring` | How many items, listed in an attribute. `estimated` says when the date is MadPlan's guess |
| `sensor.madplan_running_low` | What is below its minimum or nearly due again, listed in an attribute |
| `sensor.madplan_buy_now` | Prices low enough to act on, by the price index, listed in an attribute |
| `sensor.madplan_budget_week_expected` and `sensor.madplan_budget_month_expected` | Expected spending, with budget and remainder as attributes |
| `sensor.madplan_savings_year` | Savings |
| `sensor.madplan_price_alerts` | Triggered alerts, with the offers as an attribute |
| `sensor.madplan_notifications` | Unread messages |

The entity ids are the same whatever the language and the household's name, so the examples here
can be copied as they are. What is shown on screen follows the language. An installation from before
this keeps the ids it already has, until the entities are renamed or the integration added again.

## Dashboard

[dashboard.yaml](dashboard.yaml) is a ready-made dashboard using only
cards that come with Home Assistant. Create a new dashboard, open the raw configuration editor and
paste it in. Lists that are empty stay out of the way.

## Services

```yaml
# Buy more toilet paper
action: madplan_app.add_to_shopping_list
data:
  name: Toiletpapir

# Report stock, such as from a sensor or a barcode scanner. With min_quantity,
# MadPlan says when it is time to buy more.
action: madplan_app.update_pantry
data:
  name: Toiletpapir
  quantity: 2
  unit: stk
  min_quantity: 4

# Answer "shall we have this?". This decides in MadPlan only: what goes to Mealie waits for the
# button on the plan page. A "no" to a meal whose food is all bought is refused (409), as it can
# only be moved to another day. Each meal in the sensor's `meals` attribute says how much of its
# food is bought, in `bought`: none, partial or full.
action: madplan_app.vote_meal
data:
  meal_id: 42
  vote: "yes"

# Press "Save and send to Mealie" for the household's current plans. Only accepted meals go, and only
# when someone calls this: MadPlan never sends by itself.
action: madplan_app.send_to_mealie

# Say whether a meal was made. MadPlan assumes that accepted meals were, once the day has passed.
action: madplan_app.meal_cooked
data:
  meal_id: 42
  cooked: false
```

## Automation examples

Use the food before it goes off:

```yaml
alias: Use the food before it expires
trigger:
  - platform: time
    at: "16:00:00"
condition:
  - condition: numeric_state
    entity_id: sensor.madplan_expiring
    above: 0
action:
  - action: notify.mobile_app_my_phone
    data:
      title: Use soon
      message: >-
        {{ state_attr('sensor.madplan_expiring', 'items') | map(attribute='name') | join(', ') }}
```

Vote from the phone. This one asks about the first meal waiting for an answer, and the buttons on the
notification send the answer back:

```yaml
alias: Ask about the next meal
trigger:
  - platform: numeric_state
    entity_id: sensor.madplan_meals_to_vote
    above: 0
action:
  - variables:
      meal: "{{ state_attr('sensor.madplan_meals_to_vote', 'meals')[0] }}"
  - action: notify.mobile_app_my_phone
    data:
      title: Shall we have this?
      message: "{{ meal.date }}: {{ meal.title }}"
      data:
        actions:
          - action: "MADPLAN_YES_{{ meal.id }}"
            title: "Yes please"
          - action: "MADPLAN_NO_{{ meal.id }}"
            title: "No thanks"
---
alias: Send the answer to MadPlan
trigger:
  - platform: event
    event_type: mobile_app_notification_action
condition:
  - condition: template
    value_template: "{{ trigger.event.data.action.startswith('MADPLAN_') }}"
action:
  - action: madplan_app.vote_meal
    data:
      meal_id: "{{ trigger.event.data.action.split('_')[2] | int }}"
      vote: "{{ 'yes' if trigger.event.data.action.split('_')[1] == 'YES' else 'no' }}"
```

Send to Mealie from the phone. MadPlan already tells people the day before the first accepted meal
that has not been sent. This does it from a notification with a button:

```yaml
alias: Offer to send the plan to Mealie
trigger:
  - platform: time
    at: "18:00:00"
condition:
  - condition: numeric_state
    entity_id: sensor.madplan_meals_not_sent
    above: 0
action:
  - action: notify.mobile_app_my_phone
    data:
      title: The meal plan has not been sent to Mealie
      message: "{{ states('sensor.madplan_meals_not_sent') }} accepted meals are waiting."
      data:
        actions:
          - action: MADPLAN_SEND
            title: Send to Mealie
---
alias: Send the plan when asked
trigger:
  - platform: event
    event_type: mobile_app_notification_action
    event_data:
      action: MADPLAN_SEND
action:
  - action: madplan_app.send_to_mealie
```

## The other direction

The MadPlan app talks to Home Assistant by itself, through the Supervisor, without this
integration:

- **Notifications** go to a `notify` service: price alerts, good times to buy, food to use up, what
  is running low, a new plan to vote on, and a shopping list whose price changed. Each person picks
  their own phone in MadPlan under Settings → Features, and the app's configuration has a default.
- **Reading sensors**: with "The assistant may read entity states" on in the app's configuration,
  the assistant can look up entities, for questions like "are we out of toilet paper?". It is off by
  default, as it sends sensor names and values to the AI agent.

Mealie's own Home Assistant integration keeps working as before. When someone sends a plan, MadPlan
writes to Mealie's shopping list and calendar, so whatever Home Assistant shows from Mealie follows.

## Language

The entities and services are named in English and Danish, following Home Assistant's language.
The messages and texts in the examples above are yours to write in either.

## Versions

The integration and the app are released separately, and both can be updated whenever. Any version
of the MadPlan app works with version 0.5.0. The app's API under `/api/v1/ha` only ever gains fields,
and a test in the app's repository checks every field this integration reads, so an older
integration keeps working with a newer app.

## License

MIT, as MadPlan.
