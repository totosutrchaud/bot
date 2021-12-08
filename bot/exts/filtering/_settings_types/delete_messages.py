from contextlib import suppress
from typing import Any

from discord.errors import NotFound

from bot.exts.filtering._filter_context import Event, FilterContext
from bot.exts.filtering._settings_types.settings_entry import ActionEntry


class DeleteMessages(ActionEntry):
    """A setting entry which tells whether to delete the offending message(s)."""

    name = "delete_messages"
    description = "Whether to delete the offending message(s)."

    def __init__(self, entry_data: Any):
        self.delete: bool = entry_data

    async def action(self, ctx: FilterContext) -> None:
        """Delete the context message(s)."""
        if ctx.event not in (Event.ON_MESSAGE, Event.ON_MESSAGE_EDIT):
            return

        with suppress(NotFound):
            if ctx.message.guild:
                await ctx.message.delete()

    def __or__(self, other: ActionEntry):
        """Combines two actions of the same type. Each type of action is executed once per filter."""
        if not isinstance(other, DeleteMessages):
            return NotImplemented

        return DeleteMessages(self.delete or other.delete)

