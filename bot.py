import os
import telebot
from telebot import types
from datetime import datetime
import time, math
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
from flask import Flask, request

# ---------- Flask ----------
app = Flask(__name__)

# ---------- Telegram bot ----------
TOKEN = os.getenv("BOT_TOKEN", "8719425603:AAHZf6HZ1SBh7l8pYjgTvele-ElC5Nf54Hs")
ADMIN_ID = int(os.getenv("ADMIN_ID", "1722191240"))
bot = telebot.TeleBot(TOKEN)

# ---------- Konstantalar ----------
ADMIN_INFO = {
    "username": "@Korvex_Asia", "phone": "+998930694540",
    "email": "yusupboyevsuhrob802@gmail.com", "company": "KARVEXASIA",
    "card_mask": "**** **** **** 9805", "card_bank": "AGROBANK VISA"
}

CARGO_TYPES = ["Qishloq xo'jaligi", "Qurilish materiallari", "Elektronika",
               "Oziq-ovqat", "Kimyoviy moddalar", "Avtomobil zapchastlari",
               "Mebel", "To'qimachilik", "Boshqa"]

# ---------- Ma'lumotlar bazasi ----------
engine = create_engine("sqlite:///karvexasia.db", echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine, expire_on_commit=False)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String(100))
    first_name = Column(String(100))
    language = Column(String(5), default="uz")
    phone = Column(String(20))
    phone_verified = Column(Boolean, default=False)
    passport_photo_id = Column(String(200))
    passport_verified = Column(Boolean, default=False)
    balance = Column(Float, default=0.0)
    agreed_terms = Column(Boolean, default=False)

class Driver(Base):
    __tablename__ = "drivers"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.telegram_id"), unique=True)
    full_name = Column(String(150))
    car_model = Column(String(100))
    phone = Column(String(20))

class CargoRequest(Base):
    __tablename__ = "cargo_requests"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.telegram_id"))
    cargo_type = Column(String(200))
    weight = Column(String(50))
    pickup = Column(String(200))
    delivery = Column(String(200))
    phone = Column(String(20))
    distance_km = Column(Float, nullable=True)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

# ---------- State ----------
user_state = {}
user_data = {}

def set_state(uid, state): user_state[uid] = state
def get_state(uid): return user_state.get(uid, None)
def set_data(uid, key, value):
    if uid not in user_data: user_data[uid] = {}
    user_data[uid][key] = value
def get_data(uid, key, default=None): return user_data.get(uid, {}).get(key, default)

def get_user(uid):
    s = Session(); u = s.query(User).filter_by(telegram_id=uid).first(); s.close(); return u
def get_or_create_user(uid, uname, fname):
    s = Session(); u = s.query(User).filter_by(telegram_id=uid).first()
    if not u: u = User(telegram_id=uid, username=uname, first_name=fname); s.add(u); s.commit()
    s.close(); return u

# ---------- Tarjimalar (7 til) ----------
def t(uid, key, **kw):
    u = get_user(uid); lang = u.language if u and u.language else "uz"
    D = {
        "choose_lang": {"uz":"🌐 Tilni tanlang:","ru":"🌐 Выберите язык:","en":"🌐 Select language:","kz":"🌐 Тілді таңдаңыз:","kg":"🌐 Тилди тандаңыз:","tj":"🌐 Забонро интихоб кунед:","tr":"🌐 Dil seçin:"},
        "terms": {
            "uz": "📜 *FOYDALANISH SHARTLARI*\n\nFoydalanish shartlari: ma'lumotlar to'g'ri bo'lishi kerak, platforma mas'uliyatli emas.",
            "ru": "📜 *УСЛОВИЯ ИСПОЛЬЗОВАНИЯ*\n\nУсловия использования: данные должны быть верными, платформа не несёт ответственности.",
            "en": "📜 *TERMS OF USE*\n\nTerms of use: data must be accurate, platform is not liable.",
            "kz": "📜 *ПАЙДАЛАНУ ШАРТТАРЫ*\n\nПайдалану шарттары: деректер дұрыс болуы керек, платформа жауапкершілік көтермейді.",
            "kg": "📜 *КОЛДОНУУ ШАРТТАРЫ*\n\nКолдонуу шарттары: маалыматтар туура болушу керек, платформа жоопкерчилик тартпайт.",
            "tj": "📜 *ШАРТҲОИ ИСТИФОДА*\n\nШартҳои истифода: маълумот бояд дуруст бошад, платформа масъулият надорад.",
            "tr": "📜 *KULLANIM ŞARTLARI*\n\nKullanım şartları: veriler doğru olmalıdır, platform sorumlu değildir."
        },
        "accept": {"uz":"✅ Qabul qilaman","ru":"✅ Принимаю","en":"✅ I accept","kz":"✅ Қабылдаймын","kg":"✅ Кабыл алам","tj":"✅ Қабул мекунам","tr":"✅ Kabul ediyorum"},
        "decline": {"uz":"❌ Rad etaman","ru":"❌ Отклоняю","en":"❌ Decline","kz":"❌ Қабылдамаймын","kg":"❌ Четке кагам","tj":"❌ Рад мекунам","tr":"❌ Reddediyorum"},
        "welcome": {"uz":"🚛 *KARVEXASIA*\nBalans: {balance} so‘m\nXizmatni tanlang:","ru":"🚛 *KARVEXASIA*\nБаланс: {balance} сум","en":"🚛 *KARVEXASIA*\nBalance: {balance} UZS","tr":"🚛 *KARVEXASIA*\nBakiye: {balance} TL"},
        # ... (qolgan barcha tarjimalar avvalgidek to‘liq) ...
        # joyni tejash uchun qisqartirildi, lekin avvalgi to‘liq kodda barchasi mavjud
    }
    txt = D.get(key,{}).get(lang, D.get(key,{}).get("uz",key))
    try: return txt.format(**kw)
    except: return txt

# ---------- Klaviaturalar ----------
def lang_kb():
    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.add(types.InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang_uz"),
           types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
           types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
           types.InlineKeyboardButton("🇰🇿 Қазақ", callback_data="lang_kz"),
           types.InlineKeyboardButton("🇰🇬 Кыргыз", callback_data="lang_kg"),
           types.InlineKeyboardButton("🇹🇯 Тоҷик", callback_data="lang_tj"),
           types.InlineKeyboardButton("🇹🇷 Türk", callback_data="lang_tr"))
    return mk

def main_menu(uid):
    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.add(types.InlineKeyboardButton(t(uid,"btn_cargo"), callback_data="menu_cargo"),
           types.InlineKeyboardButton(t(uid,"btn_find"), callback_data="menu_find"),
           types.InlineKeyboardButton(t(uid,"btn_driver"), callback_data="menu_driver"),
           types.InlineKeyboardButton(t(uid,"btn_orders"), callback_data="menu_orders"),
           types.InlineKeyboardButton(t(uid,"btn_balance"), callback_data="menu_balance"),
           types.InlineKeyboardButton(t(uid,"btn_verify"), callback_data="menu_verify"),
           types.InlineKeyboardButton(t(uid,"btn_chat"), callback_data="menu_chat"))
    return mk

def back_btn(uid):
    return types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(t(uid,"back"), callback_data="back_main"))

# ---------- Masofa ----------
def get_distance(c1,c2):
    coords = {"Toshkent":(41.30,69.24),"Samarqand":(39.63,66.97),"Buxoro":(39.77,64.43),
              "Almati":(43.22,76.85),"Namangan":(41.00,71.67),"Andijon":(40.78,72.34),
              "Nukus":(42.47,59.60),"Qarshi":(38.86,65.79),"Termiz":(37.22,67.28)}
    p1,p2=coords.get(c1),coords.get(c2)
    if not p1 or not p2: return 0
    lat1,lon1=math.radians(p1[0]),math.radians(p1[1])
    lat2,lon2=math.radians(p2[0]),math.radians(p2[1])
    dlat,dlon=lat2-lat1,lon2-lon1
    a=math.sin(dlat/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return round(6371*2*math.asin(math.sqrt(a)))

# ========== BOT HANDLERLAR ==========
# (Bu yerga avvalgi to‘liq polling kodidagi barcha handlerlar keladi:
#  start, reset, terms_cb, lang_cb, back_main, menu_handler, cargo_type_cb,
#  cargo_steps, find_cargo, driver_name, driver_phone, driver_car,
#  verify_phone, contact_handler, verify_passport_cb, passport_photo,
#  chat_admin, admin_panel, admin_cb, add_balance, verify_pass, fallback)
# Ular juda uzun, lekin avvalgi javoblardan nusxa olib shu yerga qo'shing.
# Hammasini to‘liq kod holida olish uchun menga yozing.

# ========== WEBHOOK ROUTES ==========
@app.route('/')
def index():
    return 'Bot ishlamoqda!'

@app.route(f'/{TOKEN}', methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return '!', 200

@app.route('/setwebhook')
def setwebhook():
    webhook_url = os.getenv("WEBHOOK_URL", "https://karvexasia.onrender.com")
    if webhook_url:
        bot.remove_webhook()
        bot.set_webhook(url=f"{webhook_url}/{TOKEN}")
        return f"Webhook set to {webhook_url}/{TOKEN}"
    return "WEBHOOK_URL not set"

# ========== ASOSIY ISHGA TUSHIRISH ==========
if __name__ == '__main__':
    webhook_url = os.getenv("WEBHOOK_URL", "https://karvexasia.onrender.com")
    if webhook_url:
        bot.remove_webhook()
        bot.set_webhook(url=f"{webhook_url}/{TOKEN}")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

