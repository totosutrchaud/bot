from functools import cache
from typing import Any

from discord import Guild

from bot.exts.filtering._filter_context import FilterContext
from bot.exts.filtering._settings_types.settings_entry import ActionEntry


class Ping(ActionEntry):
    """A setting entry which adds the appropriate pings to the alert."""

    name = "mentions"
    description = {
        "ping_type": "Who to ping for a trigger inside the server.",
        "dm_ping_type": "Who to ping for a trigger in the bot's DMs."
    }

    def __init__(self, entry_data: Any):
        self.guild_mentions = set(entry_data["ping_type"])
        self.dm_mentions = set(entry_data["dm_ping_type"])

    async def action(self, ctx: FilterContext) -> None:
        """Add the stored pings to the alert message content."""
        mentions = self.guild_mentions if ctx.channel.guild else self.dm_mentions
        ctx.alert_content = " ".join(map(self._resolve_mention, mentions)) + " " + ctx.alert_content

    def __or__(self, other: ActionEntry):
        """Combines two actions of the same type. Each type of action is executed once per filter."""
        if not isinstance(other, Ping):
            return NotImplemented

        return Ping({
            "ping_type": self.guild_mentions | other.guild_mentions,
            "dm_ping_type": self.dm_mentions | other.dm_mentions
        })

    @staticmethod
    @cache
    def _resolve_mention(snowflake: int, guild: Guild) -> str:
        """Return a role mention if the snowflake represents a role, or a user mention otherwise."""
        if any(snowflake == role.id for role in guild.roles):
            return f"<@&{snowflake}>"
        else:
            return f"<@{snowflake}>"
