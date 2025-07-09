import time
from omni_bot_sdk.plugins.interface import (
    Bot,
    Plugin,
    PluginExcuteContext,
    PluginExcuteResponse,
    MessageType,
    PatAction
)
from pydantic import BaseModel


class PatPluginConfig(BaseModel):
    """
    拍一拍插件配置
    enabled: 是否启用该插件
    priority: 插件优先级，数值越大优先级越高
    """
    enabled: bool = False
    priority: int = 900


class PatPlugin(Plugin):
    """
    拍一拍消息处理插件
    收到拍一拍消息，立即回拍吧

    属性：
        priority (int): 插件优先级，设置为900确保在AI插件之后执行
        name (str): 插件名称标识符
    """

    priority = 900
    name = "pat-plugin"

    def __init__(self, bot: "Bot"):
        super().__init__(bot)
        self.db = bot.db
        # 记录相同的用户，不允许在2分钟内重复发送拍一拍
        self.user_pat_record = {}
        self.enabled = self.plugin_config.enabled
        # 动态优先级支持
        self.priority = getattr(self.plugin_config, "priority", self.__class__.priority)

    def get_priority(self) -> int:
        return self.priority

    async def handle_message(self, plusginExcuteContext: PluginExcuteContext) -> None:
        """
        处理接收到的消息
        文本消息，引用消息处理，其他都先不处理
        文本消息要判断是不是 at 我，或者是不是引用了我

        参数：
            context (PluginExcuteContext): 消息处理上下文信息

        返回：
            dict: 处理结果，包含：
                - response: 响应消息内容
                - handled: 是否已处理标志
        """
        message = plusginExcuteContext.get_message()
        if message.local_type == MessageType.Pat:
            context = plusginExcuteContext.get_context()
            user = context.get("user")
            if message.patted_username != user.account:
                self.logger.info("不是拍自己，忽略消息")
                return
            self.logger.info("开始处理拍一拍消息")
            # 发送拍一拍rpa action
            # 判断是否在2分钟内重复发送拍一拍
            if message.contact.display_name in self.user_pat_record:
                if (
                    time.time() - self.user_pat_record[message.contact.display_name]
                    < 120
                ):
                    self.logger.info(
                        f"用户{message.contact.display_name}在2分钟内重复发送拍一拍，拦截"
                    )
                    plusginExcuteContext.should_stop = True
                    return
            self.user_pat_record[message.contact.display_name] = time.time()
            # 从数据库中查找最后10条消息，是否包含当前用户
            rows = self.db.get_messages_by_username(
                message_db_path=message.message_db_path,
                username=(
                    message.room.username
                    if message.is_chatroom
                    else message.contact.username
                ),
            )
            # 这里用id不行，因为和联系人表里面的id是对应不上的，必须要用username
            rows = [r for r in rows if r[17] == message.contact.username]
            if len(rows) == 0:
                self.logger.warn("当前对话没有拍机器人的消息，找不到拍的对象")
                plusginExcuteContext.should_stop = True
                return
            real_name = message.title.replace(" 拍了拍我", "").strip(
                '"'
            )  # = '"根号中年 Y" 拍了拍我'
            plusginExcuteContext.add_response(
                PluginExcuteResponse(
                    plugin_name=self.name,
                    actions=[
                        PatAction(
                            target=message.target,
                            user_name=real_name,
                            is_chatroom=message.is_chatroom,
                        ),
                    ],
                )
            )
            plusginExcuteContext.should_stop = True

    def get_plugin_name(self) -> str:
        return self.name

    def get_plugin_description(self) -> str:
        return "这是一个处理拍一拍消息的插件"

    @classmethod
    def get_plugin_config_schema(cls):
        """
        返回插件配置的pydantic schema类。
        """
        return PatPluginConfig
