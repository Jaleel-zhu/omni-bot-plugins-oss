import asyncio
import os
from typing import TYPE_CHECKING
from pydantic import BaseModel

from omni_bot_sdk.plugins.interface import (
    Bot,
    Plugin,
    PluginExcuteContext,
    PluginExcuteResponse,
    DownloadImageAction,
    MessageType,
)


class ImagePluginConfig(BaseModel):
    """
    图片插件配置
    enabled: 是否启用该插件
    priority: 插件优先级，数值越大优先级越高
    """
    enabled: bool = False
    priority: int = 100


class ImagePlugin(Plugin):
    """
    图片文件下载插件实现类
    """

    priority = 100
    name = "image-plugin"

    def __init__(self, bot: "Bot"):
        super().__init__(bot)
        self.data_dir = self.bot.user_info.data_dir
        self.enabled = self.plugin_config.enabled
        # 动态优先级支持
        self.priority = getattr(self.plugin_config, "priority", self.__class__.priority)

    def get_priority(self) -> int:
        return self.priority

    async def handle_message(self, context: PluginExcuteContext) -> None:
        if not self.enabled:
            return
        message = context.get_message()
        if message.local_type == MessageType.Image:
            # image_path = os.path.join(self.data_dir, message.path)
            # TODO 这个可能会从数据库查询，是有问题的
            filename =f"{message.file_name}.dat"
            # image = await self.bot.dat_decrypt_service.await_decryption(image_path)
            self.logger.info(f"注册图片解密回调: {filename}")
            self.bot.dat_decrypt_service.register_decrypt_callback(
                filename, lambda fname, path: self.logger.info(f"图片解密成功，文件名: {fname}, 路径: {path}")
            )
            context.add_response(
                PluginExcuteResponse(
                    plugin_name=self.name,
                    handled=True,
                    should_stop=False,
                    actions=[DownloadImageAction(target=message.target)],
                )
            )

    def get_plugin_name(self) -> str:
        return self.name

    def get_plugin_description(self) -> str:
        return "这是一个用于下载和处理图片文件的插件"

    @classmethod
    def get_plugin_config_schema(cls):
        """
        返回插件配置的pydantic schema类。
        """
        return ImagePluginConfig
