from enum import auto, Enum
from datetime import timedelta
from typing import Any

import arrow
from discord import Colour
from discord.errors import Forbidden

import bot
from bot.constants import Channels
from bot.exts.filtering._filter_context import FilterContext
from bot.exts.filtering._settings_types.settings_entry import ActionEntry


class Infraction(Enum):
    """An enumeration of infraction types. The lower the value, the higher it is on the hierarchy."""
    BAN = auto
    KICK = auto
    MUTE = auto
    VOICE_BAN = auto
    WARNING = auto
    WATCH = auto
    SUPERSTAR = auto
    NOTE = auto
    NONE = auto


class InfractionAndNotification(ActionEntry):
    """
    A setting entry which specifies what infraction to issue and the notification to DM the user.

    Since a DM cannot be sent when a user is banned or kicked, these two functions need to be grouped together.
    """

    name = "infraction_and_notification"
    description = {
        "infraction_type": "The type of infraction to issue",
        "infraction_reason": "The infraction reason to send the user.",
        "infraction_duration": (
            "How long the infraction should last. "
            "Specified in the duration format the infraction command can normally take, e.g 3d1h."
        ),
        "dm_content": (
            "The content of the DM to send the user. A mention of the user will be added automatically. "
            "If sending the DM fails, will send the message in the context channel."
        ),
        "dm_embed": "The content of the embed to DM the user, along with the text in dm_content."
    }

    def __init__(self, entry_data: Any):
        if entry_data["infraction_type"]:
            self.infraction_type = Infraction[entry_data["infraction_type"].replace(" ", "_").upper()]
        else:
            self.infraction_type = Infraction.NONE
        self.infraction_reason = entry_data["infraction_reason"]
        self.infraction_duration = float(entry_data["infraction_duration"])
        self.dm_content = entry_data["dm_content"]
        self.dm_embed = entry_data["dm_embed"]

        self.superstar = entry_data.get("superstar", None)

    async def action(self, ctx: FilterContext) -> None:
        """Add the stored pings to the alert message content."""
        ctx.dm_embed.description = (
                f"Hey {ctx.author.mention}!\n" + self._merge_messages(ctx.dm_embed.description, self.dm_embed)
        )
        if not ctx.dm_embed.colour:
            ctx.dm_embed.colour = Colour.og_blurple()
        ctx.dm_text = self._merge_messages(ctx.dm_text, self.dm_content)

        try:
            await ctx.author.send(ctx.dm_text, embed=ctx.dm_embed)
        except Forbidden:
            await ctx.channel.send(ctx.dm_text, embed=ctx.dm_embed)

        msg_ctx = await bot.instance.get_context(ctx.message)
        if self.superstar:
            await msg_ctx.invoke(
                "superstar",
                ctx.author,
                arrow.utcnow() + timedelta(seconds=self.superstar[1]),
                reason=self.superstar[0]
            )

        if self.infraction_type != Infraction.NONE:
            if self.infraction_type == Infraction.BAN or not ctx.channel.guild:
                msg_ctx.channel = bot.instance.get_channel(Channels.mod_alerts)
            await msg_ctx.invoke(
                self.infraction_type.name,
                ctx.author,
                arrow.utcnow() + timedelta(seconds=self.infraction_duration),
                reason=self.infraction_reason
            )

    def __or__(self, other: ActionEntry):
        """Combines two actions of the same type. Each type of action is executed once per filter."""
        if not isinstance(other, InfractionAndNotification):
            return NotImplemented

        entry_data = {}
        if (
                self.infraction_type != other.infraction_type
                and (self.infraction_type.name == "SUPERSTAR" or other.infraction_type.name == "SUPERSTAR")
        ):
            superstar = self.superstar if self.infraction_type.name == "SUPERSTAR" else other.superstar
            other_superstar = self.superstar if self.superstar else other.superstar
            other_type = self if self.infraction_type.name != "SUPERSTAR" else other
            if other_superstar:
                entry_data["superstar"] = (
                    self._merge_messages(superstar[0], other_superstar[0]), max(superstar[1], other_superstar[1])
                )
            else:
                entry_data["superstar"] = (superstar.infraction_reason, superstar.infraction_duration)
            entry_data["infraction_type"] = other_type.infraction_type.name
            entry_data["infraction_reason"] = other_type.infraction_reason
            entry_data["infraction_duration"] = other_type.infraction_duration
            entry_data["dm_content"] = other_type.dm_content
            entry_data["dm_embed"] = other_type.dm_embed
        else:
            if self.infraction_type != other.infraction_type:
                higher = self
                lower = other
                if self.infraction_type.value > other.infraction_type.value:
                    higher, lower = lower, higher
                entry_data["infraction_type"] = higher.infraction_type.name
                entry_data["infraction_duration"] = higher.infraction_duration
            else:
                entry_data["infraction_type"] = self.infraction_type
                entry_data["infraction_duration"] = max(self.infraction_duration, other.infraction_duration)
            entry_data["infraction_reason"] = self._merge_messages(self.infraction_reason, other.infraction_reason)
            entry_data["dm_content"] = self._merge_messages(self.dm_content, other.dm_content)
            entry_data["dm_embed"] = self._merge_messages(self.dm_embed, other.dm_embed)
            entry_data["superstar"] = self.superstar if self.superstar else other.superstar

        return InfractionAndNotification(entry_data)

    @staticmethod
    def _merge_messages(message1: str, message2: str) -> str:
        """Combine two messages into bullet points of a single message."""
        if not message1 and not message2:
            return ""
        elif not message1:
            return message2
        elif not message2:
            return message1

        if not message1.startswith("•"):
            message1 = "• " + message1
        if not message2.startswith("•"):
            message2 = "• " + message2
        return f"{message1}\n\n{message2}"

