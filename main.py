from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.event.filter import EventMessageType  # 导入事件类型枚举
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from collections import defaultdict

@register("touchtorepeat", "YourName", "戳一戳时重复群内最新消息", "v1.0.1")
class TouchToRepeatPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 存储每个群的最新消息
        self.latest_messages = defaultdict(dict)

    # ✅ 修正：使用 event_message_type 监听所有消息事件
    @filter.event_message_type(EventMessageType.ALL)
    async def on_message(self, event: AstrMessageEvent):
        """监听并缓存每条消息"""
        
        # 获取消息原始数据
        raw_message = event.message_obj.raw_message
        
        # 判断是否是群消息
        group_id = raw_message.get('group_id')
        
        if group_id:
            message_content = event.message_str
            
            # 忽略命令消息和空消息
            if message_content and not message_content.startswith('/'):
                self.latest_messages[group_id] = {
                    'content': message_content,
                    'sender_name': event.get_sender_name(),
                    'sender_id': event.get_sender_id(),
                    'time': event.message_obj.timestamp
                }
                logger.debug(f"缓存群 {group_id} 的最新消息: {message_content[:50]}")

    # ✅ 修正：使用 event_message_type 监听私聊和群聊消息，然后判断是否为戳一戳
    @filter.event_message_type(EventMessageType.ALL)
    async def on_poke_handler(self, event: AstrMessageEvent):
        """处理戳一戳事件"""
        
        # 获取消息原始数据
        raw_message = event.message_obj.raw_message
        
        # 判断消息类型是否为 notice（通知事件）
        # 戳一戳事件在原始数据中的 post_type 为 "notice"，notice_type 为 "poke"
        if raw_message.get('post_type') == 'notice' and raw_message.get('notice_type') == 'poke':
            
            # 获取相关信息
            group_id = raw_message.get('group_id')
            target_id = raw_message.get('target_id')
            bot_id = event.get_self_id()
            user_id = raw_message.get('user_id')
            
            # 只响应群聊中戳机器人的事件
            if group_id and str(target_id) == str(bot_id):
                latest = self.latest_messages.get(group_id)
                
                if latest and latest.get('content'):
                    reply_msg = f"🔁 来自 {latest['sender_name']} 的最新消息：\n「{latest['content']}」"
                    yield event.plain_result(reply_msg)
                    logger.info(f"群 {group_id} 中用户 {user_id} 戳了机器人，已回复最新消息")
                else:
                    yield event.plain_result("📭 还没有缓存到消息呢，先发一条消息试试吧~")

    async def terminate(self):
        self.latest_messages.clear()
        logger.info("戳一戳重复消息插件已卸载")