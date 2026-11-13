"""Constants for the MadPlan integration."""

# Not "madplan", which another, unrelated integration also uses: the two must never overwrite
# each other's files or be mistaken for each other in Home Assistant and HACS.
DOMAIN = "madplan_app"

CONF_SCAN_MINUTES = "scan_minutes"
DEFAULT_SCAN_MINUTES = 5

SERVICE_ADD_TO_SHOPPING_LIST = "add_to_shopping_list"
SERVICE_UPDATE_PANTRY = "update_pantry"
SERVICE_VOTE_MEAL = "vote_meal"
SERVICE_MEAL_COOKED = "meal_cooked"
SERVICE_SEND_TO_MEALIE = "send_to_mealie"
