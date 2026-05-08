import telebot
from telebot import types
from datetime import datetime
import time, os, math
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker

TOKEN = "8719425603:AAHZf6HZ1SBh7l8pYjgTvele-ElC5Nf54Hs"
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

# ---------- TARJIMALAR ----------
def t(uid, key, **kw):
    u = get_user(uid); lang = u.language if u else "uz"
    D = {
        "choose_lang": {"uz":"🌐 Tilni tanlang:","ru":"🌐 Выберите язык:","en":"🌐 Select language:","kz":"🌐 Тілді таңдаңыз:","kg":"🌐 Тилди тандаңыз:","tj":"🌐 Забонро интихоб кунед:","tr":"🌐 Dil seçin:"},
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
    
    # PDF shartnomani yuborish
    pdf_path = "contracts/terms.pdf"
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            bot.send_document(uid, f, caption="📜 *Rasmiy foydalanish shartlari*\n\nIltimos, yuqoridagi hujjatni diqqat bilan o‘qing.")
    
    # Rozilik tugmalari
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton(t(uid, "accept"), callback_data="accept_terms"),
           types.InlineKeyboardButton(t(uid, "decline"), callback_data="decline_terms"))
    bot.send_message(uid, "Yuqoridagi shartlarga rozimisiz?", parse_mode="Markdown", reply_markup=mk)

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
    bot.send_message(uid, t(uid,"welcome",balance=u.balance), parse_mode="Markdown", reply_markup=main_menu(uid))  # bu yerda
@bot.callback_query_handler(func=lambda c: c.data=="back_main")
def back_main(c):
    uid=c.message.chat.id; u=get_user(uid); set_state(uid,"main")
    bot.send_message(uid, t(uid,"welcome",balance=u.balance), parse_mode="Markdown", reply_markup=main_menu(uid))

# --- Menyu tugmalari ---
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

# --- Yuk berish bosqichlari ---
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
        data={
            "cargo":get_data(uid,"cargo_type"),
            "weight":get_data(uid,"weight"),
            "pickup":get_data(uid,"pickup"),
            "delivery":get_data(uid,"delivery"),
            "phone":phone
        }
        dist=get_distance(data["pickup"],data["delivery"])
        s=Session()
        cargo=CargoRequest(user_id=uid, cargo_type=data["cargo"], weight=data["weight"],
                         pickup=data["pickup"], delivery=data["delivery"], phone=phone, distance_km=dist)
        s.add(cargo); s.commit(); s.close()
        bot.send_message(uid, t(uid,"cargo_success",cargo=data["cargo"],weight=data["weight"],
                                                 pickup=data["pickup"],delivery=data["delivery"],
                                                 phone=phone, distance=dist), parse_mode="Markdown", reply_markup=main_menu(uid))
        set_state(uid,"main")
        try: bot.send_message(ADMIN_ID, f"🔔 Yangi yuk!\n👤 {m.from_user.first_name}\n📦 {data['cargo']} | {data['weight']}t\n📍 {data['pickup']} → {data['delivery']}\n📞 {phone}")
        except: pass
        drivers = s.query(Driver).all()
        for d in drivers:
            try: bot.send_message(d.user_id, f"🔔 Yangi yuk: {data['cargo']} ({data['pickup']}→{data['delivery']}), tel: {phone}")
            except: pass

# --- Yuk qidirish ---
@bot.message_handler(func=lambda m: get_state(m.chat.id)=="find_cargo")
def find_cargo(m):
    uid=m.chat.id; city=m.text
    s=Session()
    results=s.query(CargoRequest).filter((CargoRequest.pickup.ilike(f"%{city}%")) | (CargoRequest.delivery.ilike(f"%{city}%"))).all()
    s.close()
    if results:
        txt=f"🔍 {city} bo'yicha yuklar:\n\n"
        for r in results: txt+=f"📦 {r.cargo_type} | {r.pickup}→{r.delivery} | 📞 {r.phone}\n"
    else: txt=t(uid,"no_cargo")
    bot.send_message(uid, txt, reply_markup=main_menu(uid))
    set_state(uid,"main")

# --- Haydovchi ro'yxatdan o'tish ---
@bot.message_handler(func=lambda m: get_state(m.chat.id)=="driver_name")
def driver_name(m):
    uid=m.chat.id; set_data(uid,"driver_name",m.text); set_state(uid,"driver_phone")
    bot.send_message(uid, "📞 Telefon raqamingiz:", reply_markup=back_btn(uid))

@bot.message_handler(func=lambda m: get_state(m.chat.id)=="driver_phone")
def driver_phone(m):
    uid=m.chat.id; set_data(uid,"driver_phone",m.text); set_state(uid,"driver_car")
    bot.send_message(uid, "🚛 Mashina modeli:", reply_markup=back_btn(uid))

@bot.message_handler(func=lambda m: get_state(m.chat.id)=="driver_car")
def driver_car(m):
    uid=m.chat.id; car=m.text
    s=Session()
    exist=s.query(Driver).filter_by(user_id=uid).first()
    if exist:
        exist.car_model=car; exist.phone=get_data(uid,"driver_phone"); exist.full_name=get_data(uid,"driver_name")
    else:
        d=Driver(user_id=uid, full_name=get_data(uid,"driver_name"), phone=get_data(uid,"driver_phone"), car_model=car)
        s.add(d)
    s.commit(); s.close()
    set_state(uid,"main")
    bot.send_message(uid, "✅ Haydovchi sifatida ro'yxatdan o'tdingiz!", reply_markup=main_menu(uid))

# --- Verifikatsiya ---
@bot.callback_query_handler(func=lambda c: c.data=="verify_phone")
def verify_phone(c):
    uid=c.message.chat.id
    mk=types.ReplyKeyboardMarkup(resize_keyboard=True)
    mk.add(types.KeyboardButton("📱 Raqamni yuborish", request_contact=True))
    bot.send_message(uid, "Telefon raqamingizni yuboring:", reply_markup=mk)

@bot.message_handler(content_types=['contact'])
def contact_handler(m):
    uid=m.chat.id; phone=m.contact.phone_number
    s=Session(); u=s.query(User).filter_by(telegram_id=uid).first()
    u.phone=phone; u.phone_verified=True; s.commit(); s.close()
    bot.send_message(uid, "✅ Telefon tasdiqlandi!", reply_markup=types.ReplyKeyboardRemove())

@bot.callback_query_handler(func=lambda c: c.data=="verify_passport")
def verify_passport_cb(c):
    uid=c.message.chat.id; set_state(uid,"waiting_passport")
    bot.send_message(uid, "📸 Pasport yoki ID karta rasmini yuboring:")

@bot.message_handler(content_types=['photo'], func=lambda m: get_state(m.chat.id)=="waiting_passport")
def passport_photo(m):
    uid=m.chat.id; file_id=m.photo[-1].file_id
    s=Session(); u=s.query(User).filter_by(telegram_id=uid).first()
    u.passport_photo_id=file_id; s.commit(); s.close()
    bot.send_photo(ADMIN_ID, file_id, caption=f"Pasport tekshirish\n👤 ID: {uid}")
    bot.send_message(uid, "✅ Rasm qabul qilindi. Admin tasdiqlaydi.", reply_markup=main_menu(uid))
    set_state(uid,"main")

# --- Qo'llab-quvvatlash ---
@bot.message_handler(func=lambda m: get_state(m.chat.id)=="chat_admin")
def chat_admin(m):
    uid=m.chat.id
    bot.send_message(ADMIN_ID, f"💬 Foydalanuvchi xabari (ID: {uid}):\n{m.text}")
    bot.send_message(uid, "✅ Xabar yuborildi. Admin tez orada javob beradi.", reply_markup=main_menu(uid))
    set_state(uid,"main")

# --- Admin panel ---
@bot.message_handler(commands=['admin'])
def admin_panel(m):
    if m.chat.id!=ADMIN_ID: return
    mk=types.InlineKeyboardMarkup(row_width=2)
    mk.add(types.InlineKeyboardButton("📊 Statistika", callback_data="admin_stats"),
           types.InlineKeyboardButton("📦 Yuklar", callback_data="admin_yuklar"),
           types.InlineKeyboardButton("🚛 Haydovchilar", callback_data="admin_drivers"),
           types.InlineKeyboardButton("💰 Balanslar", callback_data="admin_balance"))
    bot.send_message(ADMIN_ID, "👑 *Admin Panel*", parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_"))
def admin_cb(c):
    if c.message.chat.id!=ADMIN_ID: return
    data=c.data; s=Session()
    if data=="admin_stats":
        users=s.query(User).count(); drivers=s.query(Driver).count(); cargos=s.query(CargoRequest).count()
        txt=f"👥 Foydalanuvchilar: {users}\n🚛 Haydovchilar: {drivers}\n📦 Yuklar: {cargos}"
    elif data=="admin_yuklar":
        cargos=s.query(CargoRequest).order_by(CargoRequest.created_at.desc()).limit(20).all()
        txt="\n".join([f"📦 {c.cargo_type} | {c.pickup}→{c.delivery}" for c in cargos]) if cargos else "Yuklar yo'q"
    elif data=="admin_drivers":
        drivers=s.query(Driver).all()
        txt="\n".join([f"🚛 {d.full_name} | {d.car_model}" for d in drivers]) if drivers else "Haydovchilar yo'q"
    elif data=="admin_balance":
        users=s.query(User).all()
        txt="\n".join([f"👤 {u.first_name}: {u.balance} so'm" for u in users])
    s.close()
    bot.edit_message_text(chat_id=ADMIN_ID, message_id=c.message.message_id, text=txt, reply_markup=back_btn(ADMIN_ID))

# --- Balans to'ldirish / Pasport tasdiqlash ---
@bot.message_handler(commands=['add_balance'])
def add_balance(m):
    if m.chat.id!=ADMIN_ID: return
    try:
        _, tid, amount = m.text.split(); tid=int(tid); amount=float(amount)
        s=Session(); u=s.query(User).filter_by(telegram_id=tid).first()
        if u: u.balance+=amount; s.commit()
        s.close()
        bot.send_message(tid, f"💰 {amount} so'm hisobingizga qo'shildi. Balans: {u.balance} so'm")
        bot.send_message(ADMIN_ID, f"✅ {tid} ga {amount} so'm qo'shildi.")
    except: bot.send_message(ADMIN_ID, "Format: /add_balance <user_id> <summa>")

@bot.message_handler(commands=['verify_pass'])
def verify_pass(m):
    if m.chat.id!=ADMIN_ID: return
    try:
        _, tid, action = m.text.split(); tid=int(tid)
        s=Session(); u=s.query(User).filter_by(telegram_id=tid).first()
        if u:
            if action=="approve": u.passport_verified=True; bot.send_message(tid, "✅ Pasportingiz tasdiqlandi!")
            elif action=="reject": u.passport_verified=False; bot.send_message(tid, "❌ Pasport rad etildi.")
            s.commit()
        s.close()
    except: bot.send_message(ADMIN_ID, "Format: /verify_pass <user_id> <approve/reject>")

# --- Fallback ---
@bot.message_handler(func=lambda m: True)
def fallback(m):
    uid=m.chat.id; u=get_user(uid)
    if not u or not u.agreed_terms: start(m)
    else: bot.send_message(uid, "Iltimos, menyudan foydalaning.", reply_markup=main_menu(uid))

print("✅ KARVEXASIA professional bot ishga tushdi!")
while True:
    try: bot.polling(none_stop=True)
    except Exception as e: print(f"Xatolik: {e}"); time.sleep(5)
