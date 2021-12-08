from typing import Any

from bot.exts.filtering._filter_context import FilterContext
from bot.exts.filtering._settings_types.settings_entry import ValidationEntry


class ChannelScope(ValidationEntry):
    """A setting entry which tells whether the filter was invoked in a whitelisted channel or category."""

    name = "channel_scope"
    description = {
        "disabled_channels": "Channel IDs where the filter shouldn't trigger.",
        "disabled_categories": "Category IDs where the filter shouldn't triggered.",
        "enabled_channels": "Channel IDs where the filter should trigger even if it's disabled in the category."
    }

    def __init__(self, entry_data: Any):
        if entry_data["disabled_channels"]:
            self.disabled_channels = set(entry_data["disabled_channels"])
        else:
            self.disabled_channels = set()

        if entry_data["disabled_categories"]:
            self.disabled_categories = set(entry_data["disabled_categories"])
        else:
            self.disabled_categories = set()

        if entry_data["enabled_channels"]:
            self.enabled_channels = set(entry_data["enabled_channels"])
        else:
            self.enabled_channels = set()

    def triggers_on(self, ctx: FilterContext) -> bool:
        """
        Return whether the filter should be triggered in the given channel.

        The filter is invoked by default.
        If the channel is explicitly enabled, it bypasses the set disabled channels and categories.
        """
        channel = ctx.channel
        if hasattr(channel, "parent"):
            channel = channel.parent
        return (
                channel.id in self.enabled_channels
                or (
                        channel.id not in self.disabled_channels
                        and (not channel.category or channel.category not in self.disabled_categories)
                )
        )
