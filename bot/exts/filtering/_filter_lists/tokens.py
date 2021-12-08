import re

from bot.exts.filtering._filter_context import Event, FilterContext
from bot.exts.filtering._filter_lists.filter_list import FilterList
from bot.exts.filtering._filters.filter import Filter
from bot.exts.filtering._filters.token_filter import TokenFilter
from bot.exts.filtering._settings import Settings
from bot.exts.filtering.filtering import Filtering

SPOILER_RE = re.compile(r"(\|\|.+?\|\|)", re.DOTALL)


class TokensList(FilterList):
    """A list of filters, each looking for a specific token given by regex."""

    name = "tokens"
    description = ""

    def __init__(self, filtering_cog: Filtering):
        super().__init__(TokenFilter)
        filtering_cog.subscribe(self, Event.ON_MESSAGE, Event.ON_MESSAGE_EDIT)

    def trigger_for(self, ctx: FilterContext) -> list[Filter]:
        """Dispatch the given event to the list's filters, and return filters triggered."""
        text = ctx.content
        if SPOILER_RE.search(text):
            text = self._expand_spoilers(text)
        text = self.clean_input(text)
        ctx.content = text

        return self.filter_list_result(ctx, self.blacklist, self.blacklist_defaults)

    @staticmethod
    def _expand_spoilers(text: str) -> str:
        """Return a string containing all interpretations of a spoilered message."""
        split_text = SPOILER_RE.split(text)
        return ''.join(
            split_text[0::2] + split_text[1::2] + split_text
        )
