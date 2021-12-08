from typing import Any

from bot.exts.filtering._filter_context import FilterContext
from bot.exts.filtering._settings_types.settings_entry import ValidationEntry


class Enabled(ValidationEntry):
    """A setting entry which tells whether the filter is enabled."""

    name = "enabled"
    description = "Whether the filter is enabled."

    def __init__(self, entry_data: Any):
        self.enabled = entry_data

    def triggers_on(self, ctx: FilterContext) -> bool:
        """Return whether the filter is enabled."""
        return self.enabled
