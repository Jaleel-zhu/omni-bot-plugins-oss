import json
import tempfile
import re
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
    # 是否监听别人的加群信号
    all_room_allowed: bool = False
    # 允许处理的群列表
    allowed_room_list: list[str] = []


class WelcomePlugin(Plugin):
    """
    新用户加群，发送欢迎海报插件实现类
    """

    priority: int = 101
    name: str = "welcome-plugin"

    def __init__(self, bot: "Bot"):
        super().__init__(bot)
        self.enabled = self.plugin_config.enabled
        self.db = bot.db
        self.dify_api_key = self.plugin_config.dify_api_key
        self.dify_base_url = self.plugin_config.dify_base_url
        self.dify_client = WorkflowClient(self.dify_api_key, self.dify_base_url)
        self.all_room_allowed = self.plugin_config.all_room_allowed
        self.allowed_room_list = self.plugin_config.allowed_room_list
        # 动态优先级支持
        self.priority = getattr(self.plugin_config, "priority", self.__class__.priority)

    def get_priority(self) -> int:
        return self.priority

    def _extract_quoted_username(self, text: str, check: bool = False) -> Optional[str]:
        """
        从文本中提取被引号包裹的真实用户名

        Args:
            text: 包含用户名的文本

        Returns:
            提取到的用户名，如果没有找到则返回None

        Examples:
            - '"张三"加入了群聊' -> '张三'
            - '"李四"通过扫描你分享的二维码加入群聊' -> '李四'
            - '"李四"被邀请加入群聊' -> '李四'
            - '"王五"邀请"赵六"加入了群聊' -> '赵六' (被邀请者)
        """
        if not text:
            return None

        # 使用正则表达式匹配被双引号包裹的内容
        # 匹配模式：双引号开始，非双引号字符，双引号结束
        pattern = r'"([^"]*)"'
        matches = re.findall(pattern, text)
        if matches:
            if check and len(matches) != 2:
                self.logger.info(f"开启了校验，没有提取到两个用户名，直接返回None")
                return None
            # 如果是邀请场景（包含"邀请"关键词且有多个引号），返回最后一个用户名（被邀请者）
            if "邀请" in text and len(matches) >= 2:
                # 返回最后一个匹配的用户名（被邀请者）
                username = matches[-1].strip()
                if username:
                    return username
            else:
                # 其他情况返回第一个匹配的用户名
                username = matches[0].strip()
                if username:
                    return username

        return None

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
                # 如果是自己拉，可能是json，如果是别人拉，可能就是普通的文本字符串
                # 这如何判断是群聊呢，这里应该要加一个开关，用于明确，是否需要监听别人的加群信号，因为如果机器人加入了太多的群
                # 可能会在别的群进行处理，这里应该要添加允许处理哪些群，如果开启但是没有设置，就代表全开？
                if self.all_room_allowed:
                    # 开启了所有群的监听
                    if len(self.allowed_room_list) == 0:
                        # 不设置，就是开了全部
                        pass
                    else:
                        if message.room.username not in self.allowed_room_list:
                            self.logger.info(
                                f"{message.room.display_name} 不在允许处理的群列表中"
                            )
                            return
                else:
                    if "delchatroommember" not in message.content:
                        self.logger.info(
                            f"未开启处理全部群，不是加群消息: {message.content}"
                        )
                        return
                # 查找字符串 delchatroommember, 如果不存在就不必解析了
                if "delchatroommember" not in message.content:
                    # 按照 A邀请B的规则判断，如果不符合就直接返回 '"老胡@omni-rpa"邀请"胡言蹊"加入了群聊'
                    if "邀请" not in message.content:
                        return
                    if "加入了群聊" not in message.content:
                        return
                    if "邀请" in message.content and "加入了群聊" in message.content:
                        real_name = self._extract_quoted_username(message.content, True)
                    else:
                        return
                else:
                    content_data = json.loads(message.content)
                    sysmsg = content_data.get("sysmsg", {})
                    msg_type_key = sysmsg.get("@type")
                    if msg_type_key != "delchatroommember":
                        return
                    if msg_type_key and msg_type_key in sysmsg:
                        plain_text = sysmsg[msg_type_key].get("plain", "")

                        # 使用通用的方法提取用户名
                        real_name = self._extract_quoted_username(plain_text)

                        # 如果没有提取到用户名，记录日志并返回
                        if not real_name:
                            self.logger.info(f"无法从文本中提取用户名: {plain_text}")
                            return

                        self.logger.info(f"提取到用户名: {real_name}")
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
