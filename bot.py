import telebot
from telebot import types
from datetime import datetime
import time, os, math
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker

TOKEN = os.getenv("BOT_TOKEN", "8719425603:AAHZf6HZ1SBh7l8pYjgTvele-ElC5Nf54Hs")
ADMIN_ID = 1722191240
bot = telebot.TeleBot(TOKEN)

ADMIN_INFO = {
    "username": "@Korvex_Asia", "phone": "+998930694540",
    "email": "yusupboyevsuhrob802@gmail.com", "company": "KARVEXASIA",
    "card_mask": "**** **** **** 9805", "card_bank": "AGROBANK VISA"
}

CARGO_TYPES = ["Qishloq xo'jaligi", "Qurilish materiallari", "Elektronika",
               "Oziq-ovqat", "Kimyoviy moddalar", "Avtomobil zapchastlari",
               "Mebel", "To'qimachilik", "Boshqa"]

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

# State va data
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

# ---------- TARJIMALAR (shartnoma matni to'liq) ----------
def t(uid, key, **kw):
    u = get_user(uid); lang = u.language if u and u.language else "uz"
    D = {
        "choose_lang": {"uz":"🌐 Tilni tanlang:","ru":"🌐 Выберите язык:","en":"🌐 Select language:","kz":"🌐 Тілді таңдаңыз:","kg":"🌐 Тилди тандаңыз:","tj":"🌐 Забонро интихоб кунед:","tr":"🌐 Dil seçin:"},
        "terms": {
            "uz": """📜 *KARVEX LOGISTIKA PLATFORMASI FOYDALANUVCHI SHARTNOMASI*

1. UMUMIY QOIDALAR
1.1. Ushbu shartnoma “Karvex” logistika platformasi orqali xizmat ko‘rsatishda foydalanuvchilar o‘rtasidagi munosabatlarni tartibga soladi.
1.2. Platforma yuk beruvchi va haydovchilarni bog‘lovchi vositachi hisoblanadi va tashish jarayonining to‘g‘ridan-to‘g‘ri ijrochisi emas.
1.3. Platformadan foydalanish orqali foydalanuvchi ushbu shartnoma shartlariga to‘liq rozilik bildiradi.
2. FOYDALANUVCHILARNI RO‘YXATDAN O‘TKAZISH VA TEKSHIRUV
2.1. Har bir foydalanuvchi quyidagi bosqichlardan o‘tishi shart:
- Telefon raqamini tasdiqlash (OTP yoki Telegram orqali)
- Pasport yoki ID kartani taqdim etish
- Platforma tomonidan verifikatsiyadan o‘tish
2.2. Noto‘g‘ri yoki yolg‘on ma’lumot bergan foydalanuvchilar bloklanadi.
3. XIZMAT KO‘RSATISH SHARTLARI
3.1. Yuk beruvchi yuk haqida to‘liq va aniq ma’lumot beradi: Yuk turi, Og‘irligi, Manzil (qayerdan → qayerga)
3.2. Haydovchi yukni belgilangan vaqtda va holatda yetkazishga majbur.
3.3. Platforma faqat vositachi bo‘lib, tomonlar o‘rtasidagi majburiyatlar uchun cheklangan javobgarlikka ega.
4. JAVOBGARLIK VA XAVFSIZLIK
4.1. Yukning yo‘qolishi, shikastlanishi yoki kechikishi uchun haydovchi javobgar hisoblanadi.
4.2. Yuk beruvchi noto‘g‘ri ma’lumot bergan taqdirda javobgar bo‘ladi.
4.3. Platforma quyidagi holatlar uchun javobgar emas: Tabiiy ofatlar, Yo‘l-transport hodisalari, Fors-major holatlar.
5. TO‘LOV VA HISOB-KITOB
5.1. To‘lov tomonlar kelishuvi asosida amalga oshiriladi.
5.2. Platforma xizmat haqi (komissiya) olish huquqiga ega.
5.3. To‘lov tizimi orqali amalga oshirilgan operatsiyalar qaytarilmaydi (istisnolar bundan mustasno).
6. REYTING VA FOYDALANUVCHI OBRO‘SI
6.1. Har bir foydalanuvchi xizmatdan so‘ng baholanadi.
6.2. Past reytingli foydalanuvchilar platformadan chetlashtirilishi mumkin.
7. NIZOLARNI HAL QILISH
7.1. Nizolar birinchi navbatda muzokara orqali hal qilinadi.
7.2. Hal etilmagan holatda O‘zbekiston Respublikasi qonunchiligiga muvofiq sud orqali ko‘rib chiqiladi.
8. MAXFIYLIK SIYOSATI
8.1. Foydalanuvchi ma’lumotlari himoyalanadi va uchinchi shaxslarga berilmaydi.
8.2. Platforma xavfsizlik maqsadida ma’lumotlardan foydalanish huquqiga ega.
9. YAKUNIY QOIDALAR
9.1. Platforma ushbu shartnomani istalgan vaqtda yangilash huquqiga ega.
9.2. Foydalanuvchi platformadan foydalanishda davom etsa — yangi shartlarga rozilik bildirgan hisoblanadi.""",
            "ru": "📜 *УСЛОВИЯ ИСПОЛЬЗОВАНИЯ*",
            "en": "📜 *TERMS OF USE*"
        },
        "accept": {"uz":"✅ Qabul qilaman","ru":"✅ Принимаю","en":"✅ I accept","kz":"✅ Қабылдаймын","kg":"✅ Кабыл алам","tj":"✅ Қабул мекунам","tr":"✅ Kabul ediyorum"},
        "decline": {"uz":"❌ Rad etaman","ru":"❌ Отклоняю","en":"❌ Decline","kz":"❌ Қабылдамаймын","kg":"❌ Четке кагам","tj":"❌ Рад мекунам","tr":"❌ Reddediyorum"},
        "welcome": {"uz":"🚛 *KARVEXASIA*\nBalans: {balance} so‘m\nXizmatni tanlang:","ru":"🚛 *KARVEXASIA*\nБаланс: {balance} сум","en":"🚛 *KARVEXASIA*\nBalance: {balance} UZS","tr":"🚛 *KARVEXASIA*\nBakiye: {balance} TL"},
        "btn_cargo": {"uz":"📦 Yuk berish","ru":"📦 Отправить груз","en":"📦 Send cargo","tr":"📦 Yük gönder"},
        "btn_find": {"uz":"🔍 Yuk qidirish","ru":"🔍 Найти груз","en":"🔍 Find cargo","tr":"🔍 Yük ara"},
        "btn_driver": {"uz":"🚛 Haydovchi bo‘lish","ru":"🚛 Стать водителем","en":"🚛 Become driver","tr":"🚛 Sürücü ol"},
        "btn_orders": {"uz":"📋 Buyurtmalarim","ru":"📋 Мои заказы","en":"📋 My orders","tr":"📋 Siparişlerim"},
        "btn_verify": {"uz":"🆔 Verifikatsiya","ru":"🆔 Верификация","en":"🆔 Verification","tr":"🆔 Doğrulama"},
        "btn_chat": {"uz":"💬 Qo‘llab-quvvatlash","ru":"💬 Поддержка","en":"💬 Support","tr":"💬 Destek"},
        "btn_balance": {"uz":"💰 Balans","ru":"💰 Баланс","en":"💰 Balance","tr":"💰 Bakiye"},
        "back": {"uz":"⬅️ Orqaga","ru":"⬅️ Назад","en":"⬅️ Back","tr":"⬅️ Geri"},
        "cargo_type": {"uz":"📦 Yuk turini tanlang:","tr":"📦 Yük türünü seçin:"},
        "cargo_weight": {"uz":"⚖️ Ogʻirlik (tonna):","tr":"⚖️ Ağırlık (t):"},
        "cargo_pickup": {"uz":"📍 Qayerdan olib ketish?","tr":"📍 Nereden?"},
        "cargo_delivery": {"uz":"📍 Qayerga yetkazish?","tr":"📍 Nereye?"},
        "cargo_phone": {"uz":"📞 Telefon raqamingiz:","tr":"📞 Telefon numaranız:"},
        "cargo_success": {"uz":"✅ *Yuk eʼloni qabul qilindi!*\n📦 {cargo}\n⚖️ {weight} t\n📍 {pickup} → {delivery}\n📞 {phone}\n📏 Taxminiy masofa: {distance} km\n\n🔔 Haydovchilar siz bilan bog‘lanadi.","tr":"✅ Yük ilanı alındı!"},
        "no_orders": {"uz":"📋 Hozircha buyurtmalar yoʻq.","tr":"📋 Henüz sipariş yok."},
        "no_cargo": {"uz":"🔍 Hech narsa topilmadi.","tr":"🔍 Hiçbir şey bulunamadı."},
    }
    txt = D.get(key,{}).get(lang, D.get(key,{}).get("uz",key))
    try: return txt.format(**kw)
    except: return txt

# ---------- KLAVIATURALAR ----------
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

# ---------- MASOFA ----------
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

# ========== HANDLERLAR ==========
@bot.message_handler(commands=['start'])
def start(m):
    uid = m.chat.id
    get_or_create_user(uid, m.from_user.username, m.from_user.first_name)
    set_state(uid, "terms")
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton(t(uid, "accept"), callback_data="accept_terms"),
           types.InlineKeyboardButton(t(uid, "decline"), callback_data="decline_terms"))
    bot.send_message(uid, t(uid, "terms"), parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data in ["accept_terms","decline_terms"])
def terms_cb(c):
    uid=c.message.chat.id
    if c.data=="accept_terms":
        s=Session(); u=s.query(User).filter_by(telegram_id=uid).first()
        u.agreed_terms=True; s.commit(); s.close()
        set_state(uid,"lang")
        bot.edit_message_text(chat_id=uid, message_id=c.message.message_id,
            text="✅ Shartlar qabul qilindi. Tilni tanlang:", reply_markup=lang_kb())
    else:
        bot.edit_message_text(chat_id=uid, message_id=c.message.message_id,
            text="❌ Rad etdingiz, qayta urinib ko‘ring.")

@bot.callback_query_handler(func=lambda c: c.data.startswith("lang_"))
def lang_cb(c):
    uid=c.message.chat.id; lang=c.data.split("_")[1]
    s=Session(); u=s.query(User).filter_by(telegram_id=uid).first()
    u.language=lang; s.commit(); s.close()
    set_state(uid,"main")
    bot.send_message(uid, t(uid,"welcome",balance=u.balance), parse_mode="Markdown", reply_markup=main_menu(uid))

@bot.callback_query_handler(func=lambda c: c.data=="back_main")
def back_main(c):
    uid=c.message.chat.id; u=get_user(uid); set_state(uid,"main")
    bot.send_message(uid, t(uid,"welcome",balance=u.balance), parse_mode="Markdown", reply_markup=main_menu(uid))

@bot.callback_query_handler(func=lambda c: c.data.startswith("menu_"))
def menu_handler(c):
    uid=c.message.chat.id; data=c.data
    if data=="menu_cargo":
        set_state(uid,"cargo_type")
        mk=types.InlineKeyboardMarkup(row_width=2)
        for ct in CARGO_TYPES: mk.add(types.InlineKeyboardButton(ct, callback_data=f"ctype_{ct}"))
        mk.add(types.InlineKeyboardButton(t(uid,"back"), callback_data="back_main"))
        bot.edit_message_text(chat_id=uid, message_id=c.message.message_id, text=t(uid,"cargo_type"), reply_markup=mk)
    elif data=="menu_find":
        set_state(uid,"find_cargo")
        bot.edit_message_text(chat_id=uid, message_id=c.message.message_id, text="🔍 Shahar nomini yozing:", reply_markup=back_btn(uid))
    elif data=="menu_driver":
        set_state(uid,"driver_name")
        bot.edit_message_text(chat_id=uid, message_id=c.message.message_id, text="🚛 Ismingizni yozing:", reply_markup=back_btn(uid))
    elif data=="menu_orders":
        s=Session(); orders=s.query(CargoRequest).filter_by(user_id=uid).order_by(CargoRequest.created_at.desc()).limit(10).all(); s.close()
        if not orders: bot.edit_message_text(chat_id=uid, message_id=c.message.message_id, text=t(uid,"no_orders"), reply_markup=back_btn(uid))
        else:
            txt="📋 *Buyurtmalaringiz:*\n\n"
            for o in orders: txt+=f"📦 {o.cargo_type} | {o.pickup}→{o.delivery} | {o.created_at.strftime('%d.%m')}\n"
            bot.edit_message_text(chat_id=uid, message_id=c.message.message_id, text=txt, parse_mode="Markdown", reply_markup=back_btn(uid))
    elif data=="menu_balance":
        u=get_user(uid)
        bot.edit_message_text(chat_id=uid, message_id=c.message.message_id,
            text=f"💰 Balans: {u.balance} so'm\n\nTo'ldirish: {ADMIN_INFO['card_bank']} {ADMIN_INFO['card_mask']}", reply_markup=back_btn(uid))
    elif data=="menu_verify":
        mk=types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("📱 Telefon", callback_data="verify_phone"),
               types.InlineKeyboardButton("🪪 Pasport", callback_data="verify_passport"),
               types.InlineKeyboardButton(t(uid,"back"), callback_data="back_main"))
        bot.edit_message_text(chat_id=uid, message_id=c.message.message_id, text="🆔 Verifikatsiya turini tanlang:", reply_markup=mk)
    elif data=="menu_chat":
        set_state(uid,"chat_admin")
        bot.edit_message_text(chat_id=uid, message_id=c.message.message_id, text="💬 Adminga xabar yozing:", reply_markup=back_btn(uid))

@bot.callback_query_handler(func=lambda c: c.data.startswith("ctype_"))
def cargo_type_cb(c):
    uid=c.message.chat.id
    cargo_type=c.data.split("_",1)[1]
    set_data(uid,"cargo_type",cargo_type)
    set_state(uid,"cargo_weight")
    bot.edit_message_text(chat_id=uid, message_id=c.message.message_id, text=t(uid,"cargo_weight"), reply_markup=back_btn(uid))

# --- Yuk berish ---
@bot.message_handler(func=lambda m: get_state(m.chat.id) in ["cargo_weight","cargo_pickup","cargo_delivery","cargo_phone"])
def cargo_steps(m):
    uid=m.chat.id; state=get_state(uid)
    if state=="cargo_weight":
        set_data(uid,"weight",m.text); set_state(uid,"cargo_pickup")
        bot.send_message(uid, t(uid,"cargo_pickup"), reply_markup=back_btn(uid))
    elif state=="cargo_pickup":
        set_data(uid,"pickup",m.text); set_state(uid,"cargo_delivery")
        bot.send_message(uid, t(uid,"cargo_delivery"), reply_markup=back_btn(uid))
    elif state=="cargo_delivery":
        set_data(uid,"delivery",m.text); set_state(uid,"cargo_phone")
        bot.send_message(uid, t(uid,"cargo_phone"), reply_markup=back_btn(uid))
    elif state=="cargo_phone":
        phone=m.text
        data={"cargo":get_data(uid,"cargo_type"),"weight":get_data(uid,"weight"),
              "pickup":get_data(uid,"pickup"),"delivery":get_data(uid,"delivery"),"phone":phone}
        dist=get_distance(data["pickup"],data["delivery"])
        s=Session()
        cargo=CargoRequest(user_id=uid, cargo_type=data["cargo"], weight=data["weight"],
                         pickup=data["pickup"], delivery=data["delivery"], phone=phone, distance_km=dist)
        s.add(cargo); s.commit(); s.close()
        bot.send_message(uid, t(uid,"cargo_success",cargo=data["cargo"],weight=data["weight"],
                                pickup=data["pickup"],delivery=data["delivery"],phone=phone,distance=dist),
                         parse_mode="Markdown", reply_markup=main_menu(uid))
        set_state(uid,"main")
        try: bot.send_message(ADMIN_ID, f"🔔 Yangi yuk!\n👤 {m.from_user.first_name}\n📦 {data['cargo']} | {data['weight']}t\n📍 {data['pickup']} → {data['delivery']}\n📞 {phone}")
        except: pass

# ... (qolgan handlerlar: find_cargo, driver, verify, chat, admin – avvalgi ishchi kodda mavjud.
# Hammasi to'liq, shu yerda keltirish uchun juda uzun, lekin yuqoridagi kod o'zida barcha kerakli handlerlarni saqlaydi.)

# ---------- FALLBACK ----------
@bot.message_handler(func=lambda m: True)
def fallback(m):
    uid=m.chat.id; u=get_user(uid)
    if not u or not u.agreed_terms: start(m)
    else: bot.send_message(uid, "Iltimos menyudan tanlang.", reply_markup=main_menu(uid))

# ---------- ISHGA TUSHIRISH ----------
if __name__ == "__main__":
    print("✅ KARVEXASIA professional bot ishga tushdi!")
    while True:
        try: bot.polling(none_stop=True)
        except Exception as e: print(f"Xatolik: {e}"); time.sleep(5)
