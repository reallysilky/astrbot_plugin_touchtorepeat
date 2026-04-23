from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from collections import defaultdict

@register(
    "astrbot_plugin_touchtorepeat",
    "reallysilky",
    "戳一戳时重复群内最新消息",
    "v1.0.1", # 更新版本号以示区别
    "https://github.com/reallysilky/astrbot_plugin_touchtorepeat"
)
class TouchToRepeatPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 存储每个群的最新消息
        self.latest_messages = defaultdict(dict)
        
        # 启动调试日志
        logger.info("=" * 50)
        logger.info(" Touchtorepeat 插件初始化完成")
        logger.info("=" * 50)

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def on_message(self, event: AstrMessageEvent):
        """统一消息入口：记录并处理所有事件"""
        
        #记录收到的事件原始结构
        raw_message = event.message_obj.raw_message
        post_type = raw_message.get('post_type')
        
        # ========== 处理普通消息（用于缓存）==========
        if post_type == 'message':
            group_id = raw_message.get('group_id')
            
            if group_id:
                message_content = event.message_str
                
                # 忽略命令消息和空消息
                if message_content and not message_content.startswith('/'):
                    # 缓存消息
                    cached_info = {
                        'content': message_content,
                        'sender_name': event.get_sender_name(),
                        'sender_id': event.get_sender_id(),
                        'time': raw_message.get('time')
                    }
                    self.latest_messages[group_id] = cached_info
                    
                    logger.info(f"✅ 【缓存成功】群 {group_id} ")
                    logger.info(f"   消息内容: {message_content[:100]}")
                else:
                    logger.info(f"⚠️ 【缓存跳过】群 {group_id} 消息为空或以 '/' 开头，不缓存")
        
        # ========== 3. 处理戳一戳事件 ==========
        elif post_type == 'notice':
            notice_type = raw_message.get('notice_type')
            sub_type = raw_message.get('sub_type')
            
            # 判断是否为戳一戳事件
            if notice_type == 'notify' and sub_type == 'poke':
                logger.info("🎯 【戳一戳匹配】识别到 poke 事件！开始处理...")
                
                group_id = raw_message.get('group_id')
                target_id = raw_message.get('target_id')
                user_id = raw_message.get('user_id')
                bot_id = raw_message.get('self_id')
                
                logger.info(f"【戳一戳详情】群: {group_id} | 戳人者: {user_id} | 被戳者(target): {target_id} ")
                
                # 只响应群聊中戳机器人的事件
                if group_id and str(target_id) == str(bot_id):
                    logger.info(f"✅ 【条件满足】是戳机器人的事件，准备回复")
                    
                    # 从缓存中获取该群最新消息
                    latest = self.latest_messages.get(group_id)
                    
                    if latest and latest.get('content'):
                        reply_msg = latest['content']
                        
                        yield event.plain_result(reply_msg)
                        logger.info(f"✅ 【回复成功】已向群 {group_id} 发送重复消息")
                    else:
                        no_cache_msg = "📭 还没有缓存到消息呢，先发一条消息试试吧~"
                        logger.warning(f"⚠️ 【无缓存】群 {group_id} 没有缓存任何消息，回复提示: '{no_cache_msg}'")
                        yield event.plain_result(no_cache_msg)
                else:
                    logger.info(f"❌ 【条件不满足】不是戳机器人的事件，忽略")

            else:
                logger.info(f"非戳一戳通知事件，忽略")
        else:
            logger.info(f"未知的 post_type: {post_type}，本插件不处理")

    async def terminate(self):
        """插件卸载时清理缓存"""
        total_cached = sum(len(v) for v in self.latest_messages.values())
        self.latest_messages.clear()
        logger.info("=" * 50)
        logger.info(f"🛑 戳一戳重复消息插件已卸载，共清理 {total_cached} 条群聊缓存")
        logger.info("=" * 50)