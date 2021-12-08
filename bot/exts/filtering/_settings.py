from __future__ import annotations

from typing import Optional

from bot.exts.filtering._filter_context import FilterContext
from bot.exts.filtering._settings_types import settings_types
from bot.exts.filtering._settings_types.settings_entry import ActionEntry, ValidationEntry
from bot.log import get_logger

log = get_logger(__name__)


class Settings:
    """
    A collection of settings.

    For processing the settings parts in the database and evaluating them on given contexts.

    Each filter list and filter has its own settings.

    A filter is triggered only if all of its validation settings (e.g whether to invoke in DM) approve
    (the check returns True).

    If a filter is triggered, its action settings (e.g how to infract the user) are combined with the action settings of
    other triggered filters in the same event, and action is taken according to the combined action settings.

    A filter doesn't have to have its own settings. For every undefined setting, it falls back to the value defined in
    the filter list which contains the filter.
    """

    _already_warned: set[str] = set()

    def __init__(self, settings_data: dict):
        self._actions: dict[str, ActionEntry] = {}
        self._validations: dict[str, ValidationEntry] = {}

        for setting_name, value in settings_data.items():
            if setting_name in settings_types["action"]:
                self._actions[setting_name] = settings_types["action"][setting_name].create(value)
            elif setting_name in settings_types["validation"]:
                self._validations[setting_name] = settings_types["validation"][setting_name].create(value)
            elif setting_name not in self._already_warned:
                log.warning(f"A setting named {setting_name} was loaded from the database, but no matching class.")
                self._already_warned.add(setting_name)

    @classmethod
    def create(cls, settings_data: dict) -> Optional[Settings]:
        """
        Returns a Settings object from `settings_data` if it holds any value, None otherwise.

        Use this method to create Settings objects instead of the init.
        The None value is significant for how a filter list iterates over its filters.
        """
        settings = Settings(settings_data)
        # If an entry doesn't hold any values, its `create` method will return None.
        # If all entries are None, then the settings object holds no values.
        if not any(settings._actions) and not any(settings._validations):
            return None

        return settings

    def evaluate(self, ctx: FilterContext) -> tuple[set[str], set[str]]:
        """Evaluates for each setting whether the context is relevant to the filter."""
        passed = set()
        failed = set()

        for name, validation in self._validations.items():
            if validation:
                if validation.triggers_on(ctx):
                    passed.add(name)
                else:
                    failed.add(name)

        return passed, failed


