LOG_ACTIONS = ("view", "click", "favorite", "cart", "purchase")
SOURCE_CHANNELS = ("homepage", "search", "recommendation", "campaign")
DEVICE_TYPES = ("mobile", "desktop")

LOG_FIELD_NAMES = (
    "log_id",
    "user_id",
    "merchant_id",
    "product_id",
    "product_name",
    "category",
    "brand",
    "price",
    "action_type",
    "region",
    "device_type",
    "source_channel",
    "session_id",
    "stay_duration",
    "is_new_user",
    "timestamp",
)

ACTION_WEIGHTS = {
    "view": 45,
    "click": 20,
    "favorite": 10,
    "cart": 15,
    "purchase": 10,
}
