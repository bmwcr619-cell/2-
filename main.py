import random
import re
import os
import json
import threading
from datetime import datetime
from flask import Flask
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- إعدادات السيرفر لضمان الاستمرارية ---
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "Bot is Running Live!"

def run_flask():
    port = int(os.environ.get("PORT", 7860))
    web_app.run(host='0.0.0.0', port=port)

# --- الإعدادات الثابتة ---
TOKEN = "8546666050:AAFt7buGH1xrVTTWa-lrIhOdesG_sk2n_bM"
AU_LINK = "https://t.me/arab_union3"
DATA_FILE = "bot_data.json"

# --- القوانين التفصيلية (الدستور المحدث) ---
DETAILED_LAWS = {
    "قوائم": "⚖️ قوانين القوائم:\n1- فوز القوائم يمنع كتابة النجم والحاسم.\n2- الحاسم For Free لا يحتسب (يؤخذ من قبله).\n3- المنشن للحكم إلزامي عند إرسال القائمة.",
    "سكربت": "⚖️ قوانين السكربت:\n⬆️ طاقات 92 أو أقل = سكربت.\n⬆️ طاقات أعلى من 92 = ليس سكربت.\n⬆️ الاعتراض في بداية المباراة فقط مع دليل.",
    "وقت": "⚖️ التوقيت الرسمي:\n⏰ من 9 صباحاً حتى 1 صباحاً.\n🔥 المواجهة العادية: يومين.\n🔥 النهائي: 3 أيام.",
    "انتقالات": "⚖️ قوانين الانتقالات:\n📺 مسموحة فقط يومي (الخميس والجمعة).\n🤔 الانتقال في يوم آخر يعتبر غير رسمي ويتم تبديل اللاعب.",
    "تصوير": "⚖️ قوانين التصوير (الآيفون):\n📹 فيديو (روم المحادثة + الرقم التسلسلي من حول الجهاز).\n⚠️ يمنع التصوير نهاية المباراة لتجنب الغش.",
    "عقود": "⚖️ قوانين العقود:\n🤔 أقصى حد: 8 مسؤولين.\n🤔 الفسخ حصراً من القادة المسجلين في العقود.",
    "سب": "🚫 سب الأهل أو الكفر يؤدي للطرد والحظر المباشر."
}

# مخزن البيانات
wars = {}

def save_data():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(wars, f, ensure_ascii=False, indent=4)

def to_emoji(num):
    dic = {'0':'0️⃣','1':'1️⃣','2':'2️⃣','3':'3️⃣','4':'4️⃣','5':'5️⃣','6':'6️⃣','7':'7️⃣','8':'8️⃣','9':'9️⃣'}
    return "".join(dic.get(c, c) for c in str(num))

async def handle_war(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    cid, msg, user = update.effective_chat.id, update.message.text, update.effective_user
    msg_up = msg.upper()
    u_tag = f"@{user.username}" if user.username else f"ID:{user.id}"

    # الرد على القوانين (بشرط المنشن)
    if f"@{context.bot.username}" in msg:
        for key, law in DETAILED_LAWS.items():
            if key in msg.lower():
                await update.message.reply_text(law)
                return

    # التحقق من يوم الانتقالات
    if "انتقال" in msg:
        day = datetime.now().strftime('%A')
        if day not in ["Thursday", "Friday"]:
            await update.message.reply_text("⚠️ تنبيه: الانتقالات مسموحة فقط الخميس والجمعة!")

    # بدء المواجهة
    if "CLAN" in msg_up and "VS" in msg_up and "+1" not in msg:
        parts = msg_up.split(" VS ")
        c1 = parts[0].replace("CLAN ", "").strip()
        c2 = parts[1].replace("CLAN ", "").strip()
        wars[cid] = {"c1":{"n":c1,"s":0,"stats":[]}, "c2":{"n":c2,"s":0,"stats":[]}, "active":True}
        save_data()
        await update.message.reply_text(f"⚔️ بدأت الحرب: {c1} VS {c2}")
        return

    # تسجيل النقاط
    if cid in wars and wars[cid]["active"]:
        w = wars[cid]
        if "+1" in msg or "+ 1" in msg:
            win_k = "c1" if w["c1"]["n"].upper() in msg_up else ("c2" if w["c2"]["n"].upper() in msg_up else None)
            if win_k:
                players = re.findall(r'@\w+', msg)
                scores = re.findall(r'(\d+)', msg)
                if len(players) >= 2 and len(scores) >= 2:
                    p_win = players[0] if int(scores[0]) > int(scores[1]) else players[1]
                    w[win_k]["s"] += 1
                    w[win_k]["stats"].append({"name":p_win, "g":max(scores), "r":min(scores), "free":False})
                else: # نقطة فري
                    w[win_k]["s"] += 1
                    w[win_k]["stats"].append({"name":"Free", "free":True})
                
                save_data()
                await update.message.reply_text(f"✅ تم تسجيل نقطة لـ {w[win_k]['n']}")
                
                if w[win_k]["s"] >= 4:
                    w["active"] = False
                    real_p = [p for p in w[win_k]["stats"] if not p["free"]]
                    hasm = real_p[-1]["name"] if real_p else "إداري"
                    await update.message.reply_text(f"🎊 انتهت الحرب بفوز {w[win_k]['n']} 🎊\n🎯 الحاسم: {hasm}")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_war))
    print("✅ Bot is online...")
    app.run_polling()
