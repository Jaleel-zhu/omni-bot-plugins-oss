import json
import tempfile
from typing import Optional

import httpx
from omni_bot_sdk.clients.dify_client import WorkflowClient
from omni_bot_sdk.plugins.interface import (
    Bot,
    Plugin,
    PluginExcuteContext,
    MessageType,
    SendImageAction,
    PluginExcuteResponse,
)
from pydantic import BaseModel


class WelcomePluginConfig(BaseModel):
    """
    欢迎插件配置
    enabled: 是否启用该插件
    dify_api_key: Dify API密钥
    dify_base_url: Dify API基础URL
    priority: 插件优先级，数值越大优先级越高
    """
    enabled: bool = False
    dify_api_key: str = ""
    dify_base_url: str = ""
    priority: int = 101


class WelcomePlugin(Plugin):
    """
    新用户加群，发送欢迎海报插件实现类
    """

    priority = 101
    name = "welcome-plugin"

    def __init__(self, bot: "Bot"):
        super().__init__(bot)
        self.enabled = self.plugin_config.enabled
        self.db = bot.db
        self.dify_api_key = self.plugin_config.dify_api_key
        self.dify_base_url = self.plugin_config.dify_base_url
        self.dify_client = WorkflowClient(self.dify_api_key, self.dify_base_url)
        # 动态优先级支持
        self.priority = getattr(self.plugin_config, "priority", self.__class__.priority)

    def get_priority(self) -> int:
        return self.priority

    async def _handle_message_async(self, target, image_url) -> Optional[str]:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        temp_path = temp_file.name
        with open(temp_path, "wb") as f:
            async with httpx.AsyncClient() as client:
                response = await client.get(image_url)
                f.write(response.content)
        return temp_path

    async def handle_message(self, plusginExcuteContext: PluginExcuteContext) -> None:
        if not self.enabled:
            return
        message = plusginExcuteContext.get_message()
        if message.local_type != MessageType.System:
            return
        if message.room:
            self.logger.info(message.content)
            real_name = ""
            try:
                content_data = json.loads(message.content)
                sysmsg = content_data.get("sysmsg", {})
                msg_type_key = sysmsg.get("@type")
                if msg_type_key != "delchatroommember":
                    return
                if msg_type_key and msg_type_key in sysmsg:
                    plain_text = sysmsg[msg_type_key].get("plain", "")
                    if "加入了群聊" in plain_text:
                        parts = plain_text.split('"')
                        if len(parts) >= 2:
                            real_name = parts[-2].strip()
            except (json.JSONDecodeError, KeyError) as e:
                self.logger.error(f"解析欢迎消息内容时出错: {e}")
                return
            if not real_name:
                self.logger.info(f"不是欢迎消息或无法提取名称: {message.content}")
                return
            try:
                request_params = {
                    "inputs": {
                        "user_name": real_name,
                        "room_name": message.room.display_name,
                        "room_user_name": message.room.username,
                    },
                    "response_mode": "blocking",
                    "user": f"{message.room.username}",
                }
                completion_response = self.dify_client.run(**request_params)
                completion_response.raise_for_status()
                result = completion_response.json().get("data").get("outputs")
                workflow_result = json.loads(result.get("text", "{}"))
                if not workflow_result.get("image_urls", []):
                    self.logger.info(f"没有生成图片")
                    return
                else:
                    self.logger.info(
                        f"生成图片: {workflow_result.get('image_urls', [])}"
                    )
                    image_url = workflow_result.get("image_urls", [])[0]
                    image_path = await self._handle_message_async(
                        message.room.display_name, image_url
                    )
                    if image_path:
                        plusginExcuteContext.add_response(
                            PluginExcuteResponse(
                                plugin_name=self.name,
                                handled=True,
                                should_stop=False,
                                response={"response": "你好！有什么我可以帮你的么？"},
                                actions=[
                                    SendImageAction(
                                        image_path=image_path,
                                        target=message.room.display_name,
                                        is_chatroom=True,
                                    ),
                                ],
                            )
                        )
                    plusginExcuteContext.should_stop = True
            except Exception as e:
                self.logger.error(f"处理消息时出错, 拦截消息: {e}")
                self.logger.info(request_params)
                return

    def get_plugin_name(self) -> str:
        return self.name

    def get_plugin_description(self) -> str:
        return "邀请好友加群"

    @classmethod
    def get_plugin_config_schema(cls):
        """
        返回插件配置的pydantic schema类。
        """
        return WelcomePluginConfig
