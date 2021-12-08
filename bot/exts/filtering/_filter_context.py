from enum import Enum, auto
from typing import Optional, Union

from discord import DMChannel, Embed, Message, TextChannel, Thread, User

from dataclasses import dataclass, field


class Event(Enum):
    ON_MESSAGE: 1
    ON_MESSAGE_EDIT: 2


@dataclass
class FilterContext:
    # Input context
    event: Event  # The type of event
    author: User  # Who triggered the event
    channel: Union[TextChannel, Thread, DMChannel]  # The channel involved
    content: str  # What actually needs filtering
    message: Optional[Message]  # The message involved
    embeds: list = field(default_factory=list)  # Any embeds involved
    # Output context
    dm_text: str = field(default_factory=str)  # The content to DM the invoker
    dm_embed: Embed = field(default_factory=Embed)  # The embed to DM the invoker
    send_alert: bool = field(default=True)  # Whether to send an alert for the moderators
    alert_content: str = field(default_factory=str)  # The content of the alert
    alert_embeds: list = field(default_factory=list)  # Any embeds to add to the alert
