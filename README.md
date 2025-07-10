# omni-bot-plugins-oss 插件总览

本项目包含多个基于 omni-bot 的插件，以下是各插件及其主要功能简介：

## 注意事项

0. omni-bot-sdk 主项目使用python版本为3.12 插件应该尽可能和主项目保持一致
1. 注意配置文件需要写入到bot的config.yaml的plugins下
2. 如果引入的依赖在bot sdk中已经有了，尽量不要增加依赖，防止冲突

## 插件列表

### 1. bot-check-plugin
用于判断消息是否为 bot 处理的插件，在会话上下文中添加是否需要bot处理

### 2. chat-context-plugin
用于维护消息上下文的插件，自动维护聊天记录，在上下文中插入聊天消息，已经转换为json字符串

### 3. image-plugin
用于下载和处理图片文件的插件。目前只包含跳转到会话，不下载高清图片，可以自己实现

### 4. openai-bot-plugin
OpenAI 聊天机器人插件，集成 OpenAI API，实现 AI 对话功能。基础ai聊天

### 5. pat-plugin
处理“拍一拍”消息的插件。

### 6. video-plugin
用于下载和处理视频文件的插件。自动点击视频，进行下载

### 7. welcome-plugin
新用户加群时发送欢迎海报的插件。使用Dify工作流，自动生成欢迎海报，需要配合豆包插件

[豆包MCP](https://github.com/HuChundong/DouBaoFreeImageGen)

---

如需详细使用方法和配置说明，请参考各插件源码及注释。 