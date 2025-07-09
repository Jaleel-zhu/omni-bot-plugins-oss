from omni_bot_sdk.plugins.interface import (
    Bot,
    Plugin,
    PluginExcuteContext,
    PluginExcuteResponse,
    MessageType,
    DownloadVideoAction,
)
from pydantic import BaseModel


class VideoPluginConfig(BaseModel):
    """
    视频插件配置
    enabled: 是否启用该插件
    priority: 插件优先级，数值越大优先级越高
    """
    enabled: bool = False
    priority: int = 100


class VideoPlugin(Plugin):
    """
    视频文件下载插件实现类

    主要功能：
    - 识别消息中的视频文件
    - 下载视频文件到本地存储
    - 处理视频文件的元数据信息

    注意事项：
    - 该插件应配置为较高优先级，确保视频文件能够被及时处理
    - 需要确保有足够的存储空间用于视频文件下载
    - 需要处理视频文件下载失败的情况
    """

    priority = 100
    name = "video-plugin"

    def __init__(self, bot: "Bot"):
        super().__init__(bot)
        self.enabled = self.plugin_config.enabled
        # 动态优先级支持
        self.priority = getattr(self.plugin_config, "priority", self.__class__.priority)

    def get_priority(self) -> int:
        return self.priority

    async def handle_message(self, context: PluginExcuteContext) -> None:
        """
        处理接收到的消息，识别并下载视频文件
        """
        if not self.enabled:
            return
        message = context.get_message()
        if message.local_type == MessageType.Video:
            context.add_response(
                PluginExcuteResponse(
                    plugin_name=self.name,
                    handled=True,
                    should_stop=False,
                    response={"response": "你好！有什么我可以帮你的么？"},
                    actions=[
                        DownloadVideoAction(
                            target=message.target, is_chatroom=message.is_chatroom
                        )
                    ],
                )
            )

    def get_plugin_name(self) -> str:
        return self.name

    def get_plugin_description(self) -> str:
        return "这是一个用于下载和处理视频文件的插件"

    @classmethod
    def get_plugin_config_schema(cls):
        """
        返回插件配置的pydantic schema类。
        """
        return VideoPluginConfig
