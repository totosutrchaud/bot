from collections import defaultdict

from discord import Message
from discord.ext.commands import Cog

from bot.bot import Bot
from bot.constants import Channels
from bot.utils import scheduling
from bot.exts.filtering._filter_context import Event, FilterContext
from bot.exts.filtering._filter_lists import filter_list_types, FilterList
from bot.log import get_logger


log = get_logger(__name__)


class Filtering(Cog):
    """"""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.filter_lists: dict[str, FilterList] = {}
        self._subscriptions: defaultdict[Event, list[FilterList]] = defaultdict(list)
        self.init_task = scheduling.create_task(self.init_cog(), event_loop=self.bot.loop)

    async def init_cog(self) -> None:
        """"""
        await self.bot.wait_until_guild_available()
        already_warned = set()

        raw_filter_lists = await self.bot.api_client.get("bot/filter/filter_lists")
        for raw_filter_list in raw_filter_lists:
            list_name = raw_filter_list["name"]
            if list_name not in self.filter_lists:
                if list_name not in filter_list_types and list_name not in already_warned:
                    log.warning(f"A filter list named {list_name} was loaded from the database, but no matching class.")
                    already_warned.add(list_name)
                    continue
                self.filter_lists[list_name] = filter_list_types[list_name](self)
            self.filter_lists[list_name].add_list(raw_filter_list)

    def subscribe(self, filter_list: FilterList, *events: Event):
        """
        Subscribe a filter list to the given events.

        The filter list is added to a list for each event. When the event is triggered, the filter context will be
        dispatched to the subscribed filter lists.

        While it's possible to just make each filter list check the context's event, these are only the events a filter
        list expects to receive from the filtering cog, there isn't an actual limitation on the kinds of events a filter
        list can handle as long as the filter context is built properly. If for whatever reason we want to invoke a
        filter list outside of the usual procedure with the filtering cog, it will be more problematic if the events are
        hard-coded into each filter list.
        """
        for event in events:
            if filter_list not in self._subscriptions[event]:
                self._subscriptions[event].append(filter_list)

    @Cog.listener()
    async def on_message(self, msg: Message) -> None:
        ctx = FilterContext(Event.ON_MESSAGE, msg.author, msg.channel, msg.content, msg, msg.embeds)
        triggered = []
        for filter_list in self._subscriptions[Event.ON_MESSAGE]:
            triggered.extend(filter_list.triggers_for(ctx))
        await self.bot.instance.get_channel(Channels.mod_alerts).send("<@512354988157173763>: " + ", ".join(f"{filter_.id} ({filter_.token})") for filter_ in triggered)



def setup(bot: Bot) -> None:
    """Load the DuckPond cog."""
    bot.add_cog(Filtering(bot))
