import json
from collections import deque

from omni_bot_sdk.plugins.interface import (
    Bot,
    Plugin,
    PluginExcuteContext,
    PluginExcuteResponse,
    MessageType,
)
from pydantic import BaseModel


class ChatContextPluginConfig(BaseModel):
    """
    上下文插件配置
    enabled: 是否启用该插件
    priority: 插件优先级，数值越大优先级越高
    """

    enabled: bool = False
    priority: int = 1001


class ChatContextPlugin(Plugin):
    """
    消息上下文插件实现类
    """

    priority = 1001
    name = "chat-context-plugin"

    def __init__(self, bot: "Bot"):
        super().__init__(bot)
        self.session_messages = {}
        self.user = bot.user_info
        # 动态优先级支持
        self.priority = getattr(self.plugin_config, "priority", self.__class__.priority)

    def _get_session_messages(self, session_id):
        if session_id not in self.session_messages:
            self.session_messages[session_id] = deque(maxlen=20)
        return self.session_messages[session_id]

    def _format_message(self, message):
        sender = self.user.nickname if message.is_self else message.contact.display_name
        content = (
            message.to_text()
            if message.local_type == MessageType.Quote
            else message.parsed_content
        )
        return {
            "speaker_name": sender,
            "content": str(content or ""),
            "is_bot": message.is_self,
        }

    def _build_chat_history(self, session_id):
        messages = self._get_session_messages(session_id)
        if not messages:
            return ""
        return json.dumps(list(messages), ensure_ascii=False)

    def get_priority(self) -> int:
        return self.priority

    async def handle_message(self, plusginExcuteContext: PluginExcuteContext) -> None:
        message = plusginExcuteContext.get_message()
        context = plusginExcuteContext.get_context()
        # TODO 目前只维护了文本消息，其他消息类型暂时忽略
        if (
            message.local_type != MessageType.Text
            and message.local_type != MessageType.Quote
        ):
            return
        target = (
            message.room.username if message.is_chatroom else message.contact.username
        )
        session_messages = self._get_session_messages(target)
        formatted_message = self._format_message(message)
        session_messages.append(formatted_message)
        chat_history = self._build_chat_history(target)
        context["chat_history"] = chat_history
        # 不再调用 dify 判断是否 for bot，只维护上下文
        return

    def get_plugin_name(self) -> str:
        return self.name

    def get_plugin_description(self) -> str:
        return "这是一个用于维护消息上下文的插件"

    @classmethod
    def get_plugin_config_schema(cls):
        """
        返回插件配置的pydantic schema类。
        """
        return ChatContextPluginConfig
