from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from collections import defaultdict

@register("astrbot_plugin_touchtorepeat", "reallysilky", "戳一戳时重复群内最新消息", "1.0.0", "https://github.com/reallysilky/astrbot_plugin_reallybot")
class RepeatLatestMsgPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 存储每个群的最新消息，格式: {group_id: latest_message}
        self.latest_messages = defaultdict(dict)
        # 存储每个群的最新消息发送者信息
        self.latest_senders = defaultdict(dict)

    @filter.notice_type("poke")
    async def on_poke(self, event: AstrMessageEvent):
        """当机器人被戳一戳时触发"""
        
        # 获取原始事件数据
        raw_event = event.message_obj.raw_message
        
        # 获取戳人者和被戳者信息
        user_id = raw_event.get('user_id')
        target_id = raw_event.get('target_id')
        bot_id = event.message_obj.self_id
        
        # 获取群ID（戳一戳事件发生在群聊中）
        group_id = raw_event.get('group_id')
        
        # 只响应群聊中的戳一戳，并且是戳机器人本人
        if group_id and target_id == bot_id:
            # 获取该群的最新消息
            latest_msg = self.latest_messages.get(group_id)
            
            if latest_msg and latest_msg.get('content'):
                # 获取发送者名称
                sender_name = self.latest_senders.get(group_id, {}).get('name', '某人')
                latest_content = latest_msg['content']
                
                # 构建回复消息
                reply_msg = f"{latest_content}"
                
                # 发送回复
                yield event.plain_result(reply_msg)
                logger.info(f"群 {group_id} 中用户 {user_id} 戳了机器人，已重复最新消息:{latest_content}")
            else:
                # 没有缓存消息
                yield event.plain_result("📭 还没有缓存到任何消息，请先发一条消息吧~")
                logger.info(f"群 {group_id} 中没有缓存消息")

    @filter.event_type(MessageEventResult)  # 监听所有消息事件
    async def on_message(self, event: AstrMessageEvent):
        """监听并缓存每条消息"""
        
        # 获取消息的原始数据
        raw_message = event.message_obj.raw_message
        
        # 判断是否是群消息
        group_id = raw_message.get('group_id')
        
        if group_id:
            # 获取消息内容（纯文本）
            message_content = event.message_str
            
            # 获取发送者信息
            sender_name = event.get_sender_name()
            sender_id = event.get_sender_id()
            
            # 只缓存文本消息（可以根据需要调整）
            if message_content and not message_content.startswith('/'):  # 忽略命令消息
                # 存储最新消息
                self.latest_messages[group_id] = {
                    'content': message_content,
                    'sender_id': sender_id,
                    'time': event.message_obj.timestamp,
                    'message_id': event.message_obj.message_id
                }
                self.latest_senders[group_id] = {
                    'name': sender_name,
                    'id': sender_id
                }
                
                logger.debug(f"缓存群 {group_id} 的最新消息: {message_content[:50]}...")
            
    async def terminate(self):
        """插件卸载时清理缓存"""
        self.latest_messages.clear()
        self.latest_senders.clear()
        logger.info("重复最新消息插件已卸载，缓存已清理")