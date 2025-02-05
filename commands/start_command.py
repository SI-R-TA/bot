from pyrogram import Client, filters

@Client.on_message(filters.command("start"))
async def start_command(client, message):
    user_name = message.from_user.first_name
    await message.reply(
        f"🌟 مرحباً بك {user_name} في بوت التحقق! 🤖\n\n"
        "📱 يمكنك استخدام الأمر /verify لبدء عملية التحقق من الوثائق البيومترية الجزائرية.\n\n"
        "⚡ خدماتنا تشمل التحقق من:\n"
        "🪪 بطاقة التعريف البيومترية الجزائرية\n"
        "📘 جواز السفر البيومتري الجزائري\n"
        "🚗 رخصة السياقة البيومترية الجزائرية"
    )
