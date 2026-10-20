"""Constants for the Gira X1 integration."""

DOMAIN = "gira_x1"
CLIENT_ID = "de.homeassistant.gira_x1"
DEFAULT_UPDATE_INTERVAL = 10  # seconds, used when push callbacks are unavailable
PUSH_FALLBACK_POLL_INTERVAL = 300  # seconds, safety-net poll while push is active
CALLBACK_PORT_DEFAULT = 51888

# Function type URNs, as defined in the Gira IoT REST API documentation (chapter 9.1)
FUNCTION_SWITCH = "de.gira.schema.functions.Switch"
FUNCTION_DIMMER = "de.gira.schema.functions.KNX.Light"
FUNCTION_COLORED_LIGHT = "de.gira.schema.functions.ColoredLight"
FUNCTION_TUNABLE_LIGHT = "de.gira.schema.functions.TunableLight"
FUNCTION_COVERING = "de.gira.schema.functions.Covering"
FUNCTION_TRIGGER = "de.gira.schema.functions.Trigger"
FUNCTION_PRESS_AND_HOLD = "de.gira.schema.functions.PressAndHold"
FUNCTION_SCENE = "de.gira.schema.functions.Scene"
FUNCTION_SAUNA = "de.gira.schema.functions.SaunaHeating"
FUNCTION_HEATING_COOLING = "de.gira.schema.functions.KNX.HeatingCooling"
FUNCTION_FANCOIL = "de.gira.schema.functions.KNX.FanCoil"
FUNCTION_AUDIO = "de.gira.schema.functions.Audio"
FUNCTION_SONOS_AUDIO = "de.gira.schema.functions.Sonos.Audio"
FUNCTION_BINARY_STATUS = "de.gira.schema.functions.BinaryStatus"
FUNCTION_NUMERIC_UNSIGNED_STATUS = "de.gira.schema.functions.NumericUnsignedStatus"
FUNCTION_NUMERIC_SIGNED_STATUS = "de.gira.schema.functions.NumericSignedStatus"
FUNCTION_NUMERIC_FLOAT_STATUS = "de.gira.schema.functions.NumericFloatStatus"
FUNCTION_TEXT_STATUS = "de.gira.schema.functions.TextStatus"
FUNCTION_UNSIGNED8_VALUE = "de.gira.schema.functions.Unsigned8BitValue"
FUNCTION_SIGNED8_VALUE = "de.gira.schema.functions.Signed8BitValue"
FUNCTION_PERCENT_VALUE = "de.gira.schema.functions.PercentValue"
FUNCTION_TEMPERATURE_VALUE = "de.gira.schema.functions.TemperatureValue"
FUNCTION_UNSIGNED_VALUE = "de.gira.schema.functions.UnsignedValue"
FUNCTION_SIGNED_VALUE = "de.gira.schema.functions.SignedValue"
FUNCTION_DECIMAL_VALUE = "de.gira.schema.functions.DecimalValue"
FUNCTION_CAMERA = "de.gira.schema.functions.Camera"
FUNCTION_LINK = "de.gira.schema.functions.Link"

# Function types for which we actually create an entity that reads a value.
# The coordinator only polls GET /values for these - anything else (Camera,
# Link, system/service functions like "Externe toegang", write-only Trigger
# and Scene functions, or any future/unknown function type) is skipped
# entirely. This avoids polling errors for functions HA never displays
# anyway, and is more robust than trying to blacklist every problem type
# one by one.
POLLABLE_FUNCTIONS = frozenset(
    {
        FUNCTION_SWITCH,
        FUNCTION_DIMMER,
        FUNCTION_COLORED_LIGHT,
        FUNCTION_TUNABLE_LIGHT,
        FUNCTION_COVERING,
        FUNCTION_SAUNA,
        FUNCTION_HEATING_COOLING,
        FUNCTION_FANCOIL,
        FUNCTION_AUDIO,
        FUNCTION_SONOS_AUDIO,
        FUNCTION_BINARY_STATUS,
        FUNCTION_NUMERIC_UNSIGNED_STATUS,
        FUNCTION_NUMERIC_SIGNED_STATUS,
        FUNCTION_NUMERIC_FLOAT_STATUS,
        FUNCTION_TEXT_STATUS,
        FUNCTION_UNSIGNED8_VALUE,
        FUNCTION_SIGNED8_VALUE,
        FUNCTION_PERCENT_VALUE,
        FUNCTION_TEMPERATURE_VALUE,
        FUNCTION_UNSIGNED_VALUE,
        FUNCTION_SIGNED_VALUE,
        FUNCTION_DECIMAL_VALUE,
    }
)


def is_truthy(value) -> bool:
    """Interpret a Gira boolean-ish datapoint value."""
    return str(value) in ("1", "true", "True")
