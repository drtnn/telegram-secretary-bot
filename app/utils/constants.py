from enum import Enum


class ChatAction(str, Enum):
    subscribe = "subscribe"
    unsubscribe = "unsubscribe"


chat_action_names = {
    ChatAction.subscribe: "🕵🏻‍♂️ Подписаться",
    ChatAction.unsubscribe: "❌ Отписаться",
}
