from enum import StrEnum

class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class Theme(StrEnum):
    SYSTEM = "System"
    DARK = "Dark"
    LIGHT = "Light"
