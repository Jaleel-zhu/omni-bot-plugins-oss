import json
from omni_bot_sdk.clients.dify_client import WorkflowClient
from omni_bot_sdk.plugins.interface import (
    Bot,
    Plugin,
    PluginExcuteContext,
    MessageType,
)
from pydantic import BaseModel


class BotCheckPluginConfig(BaseModel):
    """
    bot_check_plugin 配置
    enabled: 是否启用该插件
    dify_api_key: Dify API密钥
    dify_base_url: Dify API基础URL
    nick_name: 机器人昵称
    priority: 插件优先级，数值越大优先级越高
    """

    enabled: bool = False
    dify_api_key: str = ""
    dify_base_url: str = ""
    nick_name: str = ""
    priority: int = 1002
    only_room: bool = False


class BotCheckPlugin(Plugin):
    """
    判断消息是否 for bot 的插件
    """

    priority = 1002
    name = "bot-check-plugin"

    def __init__(self, bot: "Bot"):
        super().__init__(bot)
        self.dify_api_key = self.plugin_config.dify_api_key
        self.dify_base_url = self.plugin_config.dify_base_url
        self.dify_client = WorkflowClient(self.dify_api_key, self.dify_base_url)
        self.user = bot.user_info
        self.nick_name = self.plugin_config.nick_name
        self.priority = getattr(self.plugin_config, "priority", self.__class__.priority)
        self.only_room = self.plugin_config.only_room

    def get_priority(self) -> int:
        return self.priority

    async def handle_message(self, plusginExcuteContext: PluginExcuteContext) -> None:
        # TODO 对群聊和私聊，采用不同的判别方式，参数加一个是否群聊
        message = plusginExcuteContext.get_message()
        if self.only_room and not message.is_chatroom:
            return
        if (
            message.local_type != MessageType.Text
            and message.local_type != MessageType.Quote
        ):
            return
        context = plusginExcuteContext.get_context()
        context["bot_check"] = True  # 添加一个变量，用于告诉后续的节点，已经经过了判断
        chat_history = context.get("chat_history", "")
        try:
            request_params = {
                "inputs": {
                    "chat_history": chat_history,
                    "full_name": self.user.nickname,
                    "nick_name": self.nick_name,
                    "is_chatroom": 1 if message.is_chatroom else 0,
                },
                "response_mode": "blocking",
                "user": f"{message.room.username if message.is_chatroom else message.contact.username}",
            }
            completion_response = self.dify_client.run(**request_params)
            completion_response.raise_for_status()
            result = completion_response.json().get("data").get("outputs")
            workflow_result = json.loads(result.get("text", "{}"))
            if not workflow_result.get("is_for_bot", False):
                context["not_for_bot"] = True
                return
        except Exception as e:
            context["not_for_bot"] = True
            return

    def get_plugin_name(self) -> str:
        return self.name

    def get_plugin_description(self) -> str:
        return "这是一个用于判断消息是否 for bot 的插件"

    @classmethod
    def get_plugin_config_schema(cls):
        """
        返回插件配置的pydantic schema类。
        """
        return BotCheckPluginConfig
