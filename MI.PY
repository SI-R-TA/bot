import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
from dotenv import load_dotenv
import aiohttp
from io import BytesIO
from cryptography.fernet import Fernet
import time
import pytz
from datetime import datetime
import hijri_converter
import psutil
from functools import lru_cache
import lxml.html
from deep_translator import GoogleTranslator
from commands import start_command
from flask import Flask
name=__name__


app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello from Render!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # اقرأ من متغير البيئة PORT أو استخدم 5000 كافتراضي
    app.run(debug=True, host="0.0.0.0", port=port)
# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# تحميل متغيرات البيئة
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

if not all([BOT_TOKEN, API_ID, API_HASH]):
    logger.error("تأكد من وجود جميع المتغيرات البيئية المطلوبة")
    exit()

# تهيئة timeout للطلبات
TIMEOUT = aiohttp.ClientTimeout(total=30)  # 30 ثانية

# تهيئة الروابط
class UrlEncryption:
    def __init__(self):
        self._base_url = "https://prestations.interieur.gov.dz"
        
    def get_url(self, route_name: str) -> str:
        routes = {
            'LOGIN': '/guichet/LOGIN',
            'PROFILE': '/guichet/PROFILE',
            'MA_DEMANDE': '/guichet/MA-DEMANDE',
            'CAPTCHA': '/guichet/captcha.ashx'
        }
        return f"{self._base_url}{routes.get(route_name, '')}"

url_encryption = UrlEncryption()
URL_PAGE = url_encryption.get_url('LOGIN')
PROFILE_URL = url_encryption.get_url('PROFILE')
MA_DEMANDE_URL = url_encryption.get_url('MA_DEMANDE')

# User-Agent و Referer لمحاكاة متصفح حقيقي
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"

# تعريف الأيام والأشهر
ARABIC_DAYS = {
    "Monday": "الاثنين",
    "Tuesday": "الثلاثاء",
    "Wednesday": "الأربعاء",
    "Thursday": "الخميس",
    "Friday": "الجمعة",
    "Saturday": "السبت",
    "Sunday": "الأحد"
}

ARABIC_MONTHS = {
    "January": "جانفي",
    "February": "فيفري",
    "March": "مارس",
    "April": "أفريل",
    "May": "ماي",
    "June": "جوان",
    "July": "جويلية",
    "August": "أوت",
    "September": "سبتمبر",
    "October": "أكتوبر",
    "November": "نوفمبر",
    "December": "ديسمبر"
}

HIJRI_MONTHS = {
    1: "محرم",
    2: "صفر",
    3: "ربيع الأول",
    4: "ربيع الثاني",
    5: "جمادى الأولى",
    6: "جمادى الآخرة",
    7: "رجب",
    8: "شعبان",
    9: "رمضان",
    10: "شوال",
    11: "ذو القعدة",
    12: "ذو الحجة"
}

# دالة لجلب صورة الكابتشا
async def get_captcha_image(session):
    try:
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": url_encryption._base_url,
            "Referer": URL_PAGE,
            "Connection": "keep-alive"
        }
        
        async with session.get(URL_PAGE, headers=headers, timeout=TIMEOUT) as response:
            if response.status != 200:
                logger.error(f"فشل في جلب الصفحة الرئيسية: {response.status}")
                return None, None
            
            page_content = await response.text()
            tree = lxml.html.fromstring(page_content)
            
            # استخراج القيم باستخدام lxml
            viewstate = tree.xpath("//input[@name='__VIEWSTATE']/@value")
            eventvalidation = tree.xpath("//input[@name='__EVENTVALIDATION']/@value")
            viewstategenerator = tree.xpath("//input[@name='__VIEWSTATEGENERATOR']/@value")
            
            if not viewstate or not eventvalidation:
                logger.error("لم يتم العثور على قيم VIEWSTATE أو EVENTVALIDATION")
                return None, None
            
            session.viewstate = viewstate[0]
            session.eventvalidation = eventvalidation[0]
            session.viewstategenerator = viewstategenerator[0] if viewstategenerator else ""
            
            captcha_elements = tree.xpath("//img[@id='MainContent_imgCaptcha']")
            if len(captcha_elements) > 0:
                captcha_img = captcha_elements[0]
                captcha_url = url_encryption._base_url + "/guichet/" + captcha_img.attrib['src'].lstrip('/')
                logger.debug(f"جلب CAPTCHA من: {captcha_url}")
                
                async with session.get(captcha_url, headers=headers, timeout=TIMEOUT) as captcha_response:
                    if captcha_response.status == 200:
                        image_data = await captcha_response.read()
                        return BytesIO(image_data), session
                    else:
                        logger.error(f"فشل في جلب الكابتشا. كود الحالة: {captcha_response.status}")
                        return None, None
            else:
                logger.error("لم يتم العثور على صورة CAPTCHA.")
                return None, None
                
    except aiohttp.ClientError as e:
        logger.error(f"خطأ في الاتصال: {e}")
        return None, None
    except Exception as e:
        logger.error(f"خطأ غير متوقع: {e}")
        return None, None

# دالة لتسجيل الدخول وجلب المعلومات
async def verify_and_fetch_info(num_document, nin, captcha_code, session):
    try:
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": url_encryption._base_url,
            "Referer": URL_PAGE,
            "Connection": "keep-alive"
        }

        # تسجيل الكوكيز الحالية
        cookies = {}
        for cookie in session.cookie_jar:
            cookies[cookie.key] = cookie.value
        logger.debug(f"الكوكيز قبل تسجيل الدخول: {cookies}")
        
        # بيانات النموذج
        form_data = {
            "__VIEWSTATE": getattr(session, 'viewstate', ''),
            "__EVENTVALIDATION": getattr(session, 'eventvalidation', ''),
            "__VIEWSTATEGENERATOR": getattr(session, 'viewstategenerator', ''),
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__LASTFOCUS": "",
            "ctl00$MainContent$num_document": num_document,
            "ctl00$MainContent$nin": nin,
            "ctl00$MainContent$txtimgcode": captcha_code,
            "ctl00$MainContent$valider": "تأكيد"
        }
        
        logger.info("إرسال طلب تسجيل الدخول...")
        async with session.post(URL_PAGE, data=form_data, headers=headers, timeout=TIMEOUT) as response:
            if response.status != 200:
                logger.error(f"فشل في تسجيل الدخول. كود الحالة: {response.status}")
                return None, None
            
            page_content = await response.text()
            tree = lxml.html.fromstring(page_content)
            
            # التحقق من الأخطاء باستخدام lxml
            error_messages = [
                (tree.xpath("//span[@id='MainContent_CustomValidator6']"), "رقم بطاقة التعريف او جواز السفر غير موجود"),
                (tree.xpath("//span[@id='MainContent_CustomValidator2']"), "رقم التعريف الوطني غير موجود"),
                (tree.xpath("//span[@id='MainContent_CustomValidator1']"), "عبارة خاطئة"),
                (tree.xpath("//span[@class='message-erreur']"), None),
                (tree.xpath("//span[@id='MainContent_ValidationSummary1']"), None),
                (tree.xpath("//div[@class='alert alert-danger']"), None)
            ]
            
            for error_elem, error_msg in error_messages:
                if error_elem and 'display:none' not in error_elem[0].attrib.get('style', ''):
                    error_text = error_msg or error_elem[0].text.strip()
                    logger.error(f"خطأ في تسجيل الدخول: {error_text}")
                    return None, error_text
            
            if 'MA-DEMANDE' not in page_content:
                return None, "فشل تسجيل الدخول"
            
            # جلب معلومات الملف الشخصي
            async with session.get(PROFILE_URL, headers=headers, timeout=TIMEOUT) as profile_response:
                if profile_response.status != 200:
                    logger.error(f"فشل في جلب الصفحة الشخصية. كود الحالة: {profile_response.status}")
                    return None, None
                
                profile_content = await profile_response.text()
                profile_tree = lxml.html.fromstring(profile_content)
                
                info = {}
                
                # استخراج الاسم واللقب باستخدام XPath
                nom_elements = profile_tree.xpath("//input[@id='MainContent_Nom']")
                prenom_elements = profile_tree.xpath("//input[@id='MainContent_prenom']")
                
                # الحصول على الاسم واللقب بالفرنسية
                nom_fr = nom_elements[0].attrib.get('value', 'غير متوفر') if len(nom_elements) > 0 else 'غير متوفر'
                prenom_fr = prenom_elements[0].attrib.get('value', 'غير متوفر') if len(prenom_elements) > 0 else 'غير متوفر'
                
                # ترجمة الاسم واللقب إلى العربية
                try:
                    translator = GoogleTranslator(source='fr', target='ar')
                    nom_ar = translator.translate(nom_fr) if nom_fr != 'غير متوفر' else 'غير متوفر'
                    prenom_ar = translator.translate(prenom_fr) if prenom_fr != 'غير متوفر' else 'غير متوفر'
                    info['nom'] = f"{nom_fr} - {nom_ar}"
                    info['prenom'] = f"{prenom_fr} - {prenom_ar}"
                except Exception as e:
                    logger.error(f"خطأ في الترجمة: {str(e)}")
                    info['nom'] = nom_fr
                    info['prenom'] = prenom_fr
                
                algiers_tz = pytz.timezone("Africa/Algiers")
                now_algiers = datetime.now(algiers_tz)
                
                # تحويل التاريخ الميلادي إلى هجري
                hijri = hijri_converter.Gregorian(now_algiers.year, now_algiers.month, now_algiers.day).to_hijri()
                
                day_name = ARABIC_DAYS.get(now_algiers.strftime("%A"), now_algiers.strftime("%A"))
                month_name = ARABIC_MONTHS.get(now_algiers.strftime("%B"), now_algiers.strftime("%B"))
                hijri_month_name = HIJRI_MONTHS.get(hijri.month, str(hijri.month))
                
                info['date_verification'] = (
                    f"{day_name} {hijri.day} {hijri_month_name} {hijri.year} هـ༈ۖ҉ـ\n"
                    f"الموافق {now_algiers.day} {month_name} {now_algiers.year}مِــــــــ\n"
                    f"الساعة {now_algiers.strftime('%H:%M:%S')}"
                )
                
                # جلب معلومات الطلب
                async with session.get(MA_DEMANDE_URL, headers=headers, timeout=TIMEOUT) as demande_response:
                    if demande_response.status != 200:
                        logger.error(f"فشل في جلب صفحة الطلب. كود الحالة: {demande_response.status}")
                        return None, None
                    
                    demande_content = await demande_response.text()
                    demande_tree = lxml.html.fromstring(demande_content)
                    
                    info['status'] = demande_tree.xpath("//span[@id='lblEtatDemande']")[0].text.strip() if demande_tree.xpath("//span[@id='lblEtatDemande']") else "غير متوفر"
                    info['date_depot'] = demande_tree.xpath("//span[@id='lblDateDepot']")[0].text.strip() if demande_tree.xpath("//span[@id='lblDateDepot']") else "غير متوفر"
                    info['lieu_depot'] = demande_tree.xpath("//span[@id='lblLieuDepot']")[0].text.strip() if demande_tree.xpath("//span[@id='lblLieuDepot']") else "غير متوفر"
                    
                    return info, None
        
    except aiohttp.ClientError as e:
        logger.error(f"خطأ في الاتصال: {e}")
        return None, f"خطأ في الاتصال: {e}"
    except Exception as e:
        logger.error(f"خطأ غير متوقع: {e}")
        return None, f"خطأ غير متوقع: {e}"

# قاموس لتخزين حالة كل مستخدم
user_states = {}

# تهيئة البوت
app = Client(
    "my_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# معالجة الأمر /start
@app.on_message(filters.command("start"))
async def start(client, message):
    await start_command(client, message)

# معالجة الأمر /login
@app.on_message(filters.command("login"))
async def login(client, message):
    user_name = message.from_user.first_name
    await message.reply(
        f"⚠️ عذراً {user_name}!\n\n"
        "🔒 خيار تسجيل الدخول غير متاح حالياً⏳\n"
        "📢 في حال إتاحة الخدمة سيتم الإعلان عن ذلك في:\n"
        "• قناة <a href='https://t.me/SIRTA_Dz'>SIRTA Algeria</a>\n"
        "• مجموعة <a href='https://www.facebook.com/groups/wisedz'>WISE Algeria</a> على Facebook\n\n"
        "💡 إذا لديك ملاحظات بعد تجربة البوت، يرجى إرسالها إلينا",
        disable_web_page_preview=True
    )

# معالجة الأمر /verify
@app.on_message(filters.command("verify"))
async def verify(client, message):
    try:
        user_id = message.from_user.id
        
        # إغلاق الجلسة السابقة إذا كانت موجودة
        if user_id in user_states and 'session' in user_states[user_id]:
            await user_states[user_id]['session'].close()
        
        # إنشاء جلسة جديدة مع timeout
        user_states[user_id] = {
            'step': 'waiting_for_document',
            'document_number': '',
            'nin': '',
            'session': aiohttp.ClientSession(timeout=TIMEOUT)
        }
        
        await message.reply("الرجاء إدخال<b> رقم بطاقة التعريف</b> او<b> جواز السفر</b> او<b> رخصة السياقة البيومترية</b>:")
    except Exception as e:
        logger.error(f"خطأ في معالجة أمر verify: {e}")
        await message.reply("حدث خطأ. الرجاء المحاولة مرة أخرى.")

# معالجة الزر start_verify
@app.on_callback_query(filters.regex("^start_verify$"))
async def start_verify_callback(client, callback_query):
    await callback_query.answer()
    await verify(client, callback_query.message)

# معالجة زر تغيير الكابتشا
@app.on_callback_query(filters.regex("^refresh_captcha$"))
async def refresh_captcha(client, callback_query):
    try:
        user_id = callback_query.from_user.id
        if user_id not in user_states:
            await callback_query.answer("⚠️ انتهت الجلسة. الرجاء بدء عملية التحقق من جديد باستخدام /verify", show_alert=True)
            return
            
        state = user_states[user_id]
        if state['step'] != 'waiting_for_captcha':
            await callback_query.answer("لا يمكن تغيير الكابتشا في هذه المرحلة", show_alert=True)
            return
            
        if state.get('last_captcha_msg'):
            try:
                await state['last_captcha_msg'].delete()
            except Exception as e:
                logger.error(f"خطأ في حذف الرسالة السابقة: {e}")
        
        captcha_image, session = await get_captcha_image(state['session'])
        if captcha_image:
            state['session'] = session
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄", callback_data="refresh_captcha")]
            ])
            
            new_msg = await callback_query.message.reply_photo(
                photo=captcha_image,
                caption="أدخل رمز التحقق المكون من 5 أرقام",
                reply_markup=keyboard
            )
            state['last_captcha_msg'] = new_msg
            await callback_query.answer("تم تحديث رمز التحقق")
        else:
            await callback_query.answer("فشل في جلب رمز التحقق الجديد", show_alert=True)
            
    except Exception as e:
        logger.error(f"خطأ في تحديث الكابتشا: {e}")
        await callback_query.answer("حدث خطأ في تحديث رمز التحقق", show_alert=True)

# معالجة الرسائل النصية
@app.on_message(filters.text & ~filters.command(["start", "verify", "login"]))
async def handle_message(client, message):
    try:
        user_id = message.from_user.id
        
        if user_id not in user_states:
            await message.reply(
                "⚠️ لم يتم بدء عملية التحقق بعد!\n\n"
                "🔹 الرجاء استخدام الأمر /verify لبدء عملية التحقق من الوثائق البيومترية الجزائرية\n"
                "🔸 سيتم توجيهك خطوة بخطوة خلال العملية"
            )
            return
            
        state = user_states[user_id]
        
        if state['step'] == 'waiting_for_document':
            # التحقق من طول رقم الوثيقة فقط (يمكن أن يحتوي على أحرف وأرقام)
            if len(message.text) != 9:
                await message.reply("<b> رقم الوثيقة</b> غير صالح. يجب أن يكون <b> 9</b> خانات")
                return
            
            state['document_number'] = message.text.upper()  # تحويل الأحرف إلى كبيرة
            state['step'] = 'waiting_for_nin'
            await message.reply("الرجاء إدخال <b>رقم التعريف الوطني:</b>")
            
        elif state['step'] == 'waiting_for_nin':
            # التحقق من صحة رقم التعريف الوطني
            if not message.text.isdigit() or len(message.text) != 18:
                await message.reply("<b>رقم التعريف الوطني </b> غير صالح. يجب أن يكون<b>18</b> رقم")
                return
            
            state['nin'] = message.text
            state['step'] = 'waiting_for_captcha'
            
            captcha_image, session = await get_captcha_image(state['session'])
            if captcha_image:
                state['session'] = session
                await message.reply("أدخل رمز التحقق المكون من <b>5</b> أرقام")
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄", callback_data="refresh_captcha")]
                ])
                
                captcha_msg = await message.reply_photo(
                    photo=captcha_image,
                    caption="افتح الصورة للرؤية الواضحة",
                    reply_markup=keyboard
                )
                state['last_captcha_msg'] = captcha_msg
            else:
                await message.reply(
                    "❌ فشل في جلب رمز التحقق\n\n"
                    "🔄 الرجاء المحاولة مرة أخرى باستخدام /verify\n"
                    "💡 تأكد من اتصالك بالإنترنت وحاول مجدداً"
                )
                del user_states[user_id]
                
        elif state['step'] == 'waiting_for_captcha':
            captcha_code = message.text
            
            # التحقق من طول رمز التحقق
            if len(captcha_code) != 5 or not captcha_code.isdigit():
                await message.reply("يجب إدخال 5 أرقام فقط. الرجاء المحاولة مرة أخرى.")
                return
            
            await message.reply("تم استلام طلبك، جاري التحقق...")
            await message.reply("🪪")
            start_time = time.time()
            
            info, error = await verify_and_fetch_info(
                state['document_number'],
                state['nin'],
                captcha_code,
                state['session']
            )
            
            # التحقق من وقت الاستجابة
            response_time = time.time() - start_time
            if response_time > 1:  # إذا استغرق أكثر من ثانية
                user_name = message.from_user.first_name
                await message.reply(
                    f"شكراً <b>{user_name}</b> لوقتك الثمين ⏳ نعتذر عن التأخير في التحقق، نسأل الله أن يعيننا على قضاء حوائجك نأمل أن نكون عند حسن ظنك دائماً، ونسأل الله لنا ولكم علما نافعا ورزقاً وعملاً طيبين، والحمد لله على هذه النعمة، أدامها الله علينا"
                )
            
            if error:
                await message.reply(
                    f"❌ حدث خطأ: {error}\n\n"
                    "🔄 الرجاء المحاولة مرة أخرى باستخدام /verify\n"
                    "💡 تأكد من صحة البيانات المدخلة"
                )
            else:
                algiers_tz = pytz.timezone("Africa/Algiers")
                now_algiers = datetime.now(algiers_tz)
                
                day_name = ARABIC_DAYS.get(now_algiers.strftime("%A"), now_algiers.strftime("%A"))
                month_name = ARABIC_MONTHS.get(now_algiers.strftime("%B"), now_algiers.strftime("%B"))
                
                hijri = hijri_converter.Gregorian(now_algiers.year, now_algiers.month, now_algiers.day).to_hijri()
                hijri_month_name = HIJRI_MONTHS.get(hijri.month, str(hijri.month))
                
                response_message = f"""👤 معلومات الحساب:
الاسم: <b>{info['prenom']}</b>
اللقب: <b>{info['nom']}</b>

📅 تاريخ التحقق:
{day_name} {hijri.day} {hijri_month_name} {hijri.year} هـ༈ۖ҉ـ
الموافق {now_algiers.day} {month_name} {now_algiers.year}مِــــــــ
الساعة {now_algiers.strftime('%H:%M:%S')}"""
                await message.reply(response_message)
            
            if user_id in user_states:
                if 'session' in user_states[user_id]:
                    await user_states[user_id]['session'].close()
                del user_states[user_id]
                
    except Exception as e:
        logger.error(f"خطأ في معالجة الرسالة: {e}")
        await message.reply(
            "⚠️ عذراً، حدث خطأ غير متوقع\n\n"
            "🔄 الرجاء المحاولة مرة أخرى باستخدام /verify\n"
            "💡 إذا استمرت المشكلة، يرجى الانتظار قليلاً ثم المحاولة مجدداً"
        )
        if user_id in user_states:
            if 'session' in user_states[user_id]:
                await user_states[user_id]['session'].close()
            del user_states[user_id]

# تشغيل البوت
if __name__ == '__main__':
    logger.info("جارٍ تشغيل البوت...")
    app.run()
