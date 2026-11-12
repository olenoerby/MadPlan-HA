# MadPlan for Home Assistant

The Home Assistant integration for [MadPlan](https://github.com/olenoerby/MadPlan), a self-hosted
meal planner for Danish households built around current supermarket offers. It shows the meal plan,
the shopping list, the pantry and the budget in Home Assistant, and lets people vote on meals, say
what was made and send the plan to Mealie from their phone.

It needs a running MadPlan server. The integration only talks to that server, with a personal token.

## Install

1. In HACS, open the menu → **Custom repositories**, add `https://github.com/olenoerby/MadPlan-HA`
   with the type **Integration**, then download **MadPlan** and restart Home Assistant.
2. In MadPlan: **Settings → Home Assistant → Create token**. Copy it, as it is only shown once.
3. In Home Assistant: **Settings → Devices & services → Add integration → MadPlan**. Enter the
   token and an address that does not pass a Cloudflare login, such as `http://<server>:6219`.

To appear in the HACS store without the custom-repository step, the repository must be public, have
a GitHub release, pass the `HACS validation` and `hassfest` checks in `.github/workflows/validate.yml`, and be
submitted to [hacs/default](https://github.com/hacs/default). Icons shown in the store need a
submission to [home-assistant/brands](https://github.com/home-assistant/brands). Those are steps
for the repository owner.

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
action: madplan.add_to_shopping_list
data:
  name: Toiletpapir

# Report stock, such as from a sensor or a barcode scanner. With min_quantity,
# MadPlan says when it is time to buy more.
action: madplan.update_pantry
data:
  name: Toiletpapir
  quantity: 2
  unit: stk
  min_quantity: 4

# Answer "shall we have this?". This decides in MadPlan only: what goes to Mealie waits for the
# button on the plan page. A "no" to a meal whose food is all bought is refused (409), as it can
# only be moved to another day. Each meal in the sensor's `meals` attribute says how much of its
# food is bought, in `bought`: none, partial or full.
action: madplan.vote_meal
data:
  meal_id: 42
  vote: "yes"

# Press "Gem og Send til Mealie" for the household's current plans. Only accepted meals go, and only
# when someone calls this: MadPlan never sends by itself.
action: madplan.send_to_mealie

# Say whether a meal was made. MadPlan assumes that accepted meals were, once the day has passed.
action: madplan.meal_cooked
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
      title: Brug snart
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
      title: Skal vi have det?
      message: "{{ meal.date }}: {{ meal.title }}"
      data:
        actions:
          - action: "MADPLAN_YES_{{ meal.id }}"
            title: "Ja tak"
          - action: "MADPLAN_NO_{{ meal.id }}"
            title: "Nej tak"
---
alias: Send the answer to MadPlan
trigger:
  - platform: event
    event_type: mobile_app_notification_action
condition:
  - condition: template
    value_template: "{{ trigger.event.data.action.startswith('MADPLAN_') }}"
action:
  - action: madplan.vote_meal
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
      title: Madplanen er ikke sendt til Mealie
      message: "{{ states('sensor.madplan_meals_not_sent') }} godkendte måltider venter."
      data:
        actions:
          - action: MADPLAN_SEND
            title: Send til Mealie
---
alias: Send the plan when asked
trigger:
  - platform: event
    event_type: mobile_app_notification_action
    event_data:
      action: MADPLAN_SEND
action:
  - action: madplan.send_to_mealie
```

## The other direction

MadPlan can also reach out to Home Assistant, set up on Admin → Integrations with a long-lived token:

- **Notifications**: these go to a `notify` service: price alerts, good times to buy, food to use up,
  what is running low, a new plan to vote on, and a shopping list whose price changed. Each user can
  switch them off under Settings → Features. With `MADPLAN_PUBLIC_URL` set to the site's real address,
  the messages end with a link to the right page.
- **Reading sensors**: when switched on, the assistant can look up entities. That is what makes
  questions like "are we out of toilet paper?" possible. It is off by default, as it shares sensor
  names and values with OpenAI when the assistant is used.

Mealie's own Home Assistant integration keeps working as before. When someone sends a plan, MadPlan
writes to Mealie's shopping list and calendar, so whatever Home Assistant shows from Mealie follows.

## Versions

The integration and the server are released separately. Version 0.4.0 needs a MadPlan server from
November 2026 or later for `send_to_mealie` and `sensor.madplan_meals_not_sent`. Older servers leave
that sensor at 0, and the service answers with an error.

## License

MIT, as MadPlan.
