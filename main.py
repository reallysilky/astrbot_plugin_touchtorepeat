from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from collections import defaultdict

@register("touchtorepeat", "YourName", "戳一戳时重复群内最新消息", "v1.0.2")
class TouchToRepeatPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 存储每个群的最新消息
        self.latest_messages = defaultdict(dict)

    async def on_message_handler(self, event: AstrMessageEvent):
        """监听所有消息事件（包括普通消息和通知事件）"""
        
        # 获取消息原始数据
        raw_message = event.message_obj.raw_message
        
        # 获取 post_type 判断事件类型
        post_type = raw_message.get('post_type')
        
        # ========== 处理普通消息（用于缓存）==========
        if post_type == 'message':
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
                        'time': raw_message.get('time')
                    }
                    logger.debug(f"缓存群 {group_id} 的最新消息: {message_content[:50]}")
        
        # ========== 处理戳一戳事件 ==========
        elif post_type == 'notice':
            notice_type = raw_message.get('notice_type')
            sub_type = raw_message.get('sub_type')
            
            # 判断是否为戳一戳事件（notice_type='notify' 且 sub_type='poke'）
            if notice_type == 'notify' and sub_type == 'poke':
                group_id = raw_message.get('group_id')
                target_id = raw_message.get('target_id')
                user_id = raw_message.get('user_id')
                
                # 获取机器人自身ID
                bot_id = raw_message.get('self_id')
                
                # 只响应群聊中戳机器人的事件
                if group_id and str(target_id) == str(bot_id):
                    latest = self.latest_messages.get(group_id)
                    
                    if latest and latest.get('content'):
                        reply_msg = f"{latest['content']}"
                        yield event.plain_result(reply_msg)
                        logger.info(f"群 {group_id} 中用户 {user_id} 戳了机器人，已回复最新消息:latest['content']")
                    else:
                        yield event.plain_result("📭 还没有缓存到消息呢，先发一条消息试试吧~")
                        logger.info(f"群 {group_id} 中没有缓存消息")

    async def terminate(self):
        """插件卸载时清理缓存"""
        self.latest_messages.clear()
        logger.info("戳一戳重复消息插件已卸载")