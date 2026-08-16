from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# ==================== إعدادات الواتساب الهامة ====================
# ضع رابط الـ API الخاص بحسابك بدقة (مثال: https://ultramsg.com)
API_URL = "https://ultramsg.com"
# ضع هنا رمز الأمان (Token) الخاص بحسابك في منصة الواتساب
TOKEN = "your_secret_token_here"
# ============================================================

# قاعدة بيانات مؤقتة لتخزين "حالة" كل رقم وبياناته في الذاكرة
user_states = {}

def send_whatsapp_message(to_phone, text):
    payload = {
        "token": TOKEN, 
        "to": to_phone, 
        "body": text
    }
    try:
        response = requests.post(API_URL, data=payload, timeout=10)
        print(f"حالة الإرسال إلى {to_phone}: {response.status_code}")
    except Exception as e:
        print(f"خطأ في إرسال الرسالة إلى {to_phone}: {e}")

@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    data = request.json
    if not data:
        return jsonify({"status": "no_data"}), 400
        
    # استخراج رقم المرسل ونص الرسالة (تأكد من توافق الأسماء مع منصتك)
    phone = data.get("from") or data.get("data", {}).get("from")
    message = data.get("body") or data.get("data", {}).get("body", "")
    
    if message:
        message = str(message).strip()

    if not phone or not message:
        return jsonify({"status": "ignored"}), 200

    # 1. مرحلة الترحيب بالرقم الجديد
    if phone not in user_states:
        user_states[phone] = {"stage": "welcome", "type": None}
        welcome_text = (
            "مرحباً بك في وكالة المواهب! 🌟\n\n"
            "يرجى تحديد هويتك لتوجيهك بشكل صحيح:\n"
            "1️⃣ - أنا ممثل/موهبة أرغب بالانضمام للوكالة.\n"
            "2️⃣ - أنا عميل / شركة إنتاج وأبحث عن مواهب."
        )
        send_whatsapp_message(phone, welcome_text)
        return jsonify({"status": "success"}), 200

    current_stage = user_states[phone]["stage"]

    # 2. فرز المستخدم (موهبة أم عميل) بناءً على اختياره
    if current_stage == "welcome":
        if message == "1":
            user_states[phone]["stage"] = "ask_name"
            user_states[phone]["type"] = "talent"
            send_whatsapp_message(phone, "أهلاً بك معنا! لنبدأ خطوات التسجيل.\nالرجاء كتابة اسمك الثلاثي:")
        elif message == "2":
            user_states[phone]["stage"] = "client_handling"
            user_states[phone]["type"] = "client"
            send_whatsapp_message(phone, "أهلاً وسهلاً بك يا فندم. يرجى كتابة اسم الشركة ونوع المشروع (مسلسل، إعلان، فيلم) وسيقوم أحد عملائنا بالتواصل معك فوراً.")
            del user_states[phone]  # إنهاء الجلسة للعميل ليتابع معه موظف بشري
        else:
            send_whatsapp_message(phone, "عذراً، يرجى اختيار الرقم 1 أو 2 فقط لتوجيهك.")
        return jsonify({"status": "success"}), 200

    # 3. استكمال خطوات تجميع بيانات الموهبة بالتوالي
    if user_states[phone].get("type") == "talent":
        if current_stage == "ask_name":
            user_states[phone]["name"] = message
            user_states[phone]["stage"] = "ask_age"
            send_whatsapp_message(phone, f"تشرفنا يا {message}. كم عمرك؟")
            
        elif current_stage == "ask_age":
            user_states[phone]["age"] = message
            user_states[phone]["stage"] = "ask_photos"
            send_whatsapp_message(phone, "ممتاز. الرجاء إرسال صور حديثة لك أو روابط صور واضحة لوجهك وطولك:")
            
        elif current_stage == "ask_photos":
            user_states[phone]["photos"] = message 
            user_states[phone]["stage"] = "ask_showreel"
            send_whatsapp_message(phone, "أخيراً، يرجى إرسال رابط الـ Showreel الخاص بك (يوتيوب، قوقل درايف، إلخ):")
            
        elif current_stage == "ask_showreel":
            user_states[phone]["showreel"] = message
            
            # طباعة البيانات المستلمة في خادم لوحة التحكم كإثبات نجاح للتسجيل
            print(f"🎉 تم استقبال موهبة جديدة بنجاح:\n"
                  f"الاسم: {user_states[phone]['name']}\n"
                  f"العمر: {user_states[phone]['age']}\n"
                  f"الروابط: {user_states[phone]['showreel']}")
            
            send_whatsapp_message(phone, "شكراً لك! تم تسجيل بياناتك بنجاح في وكالتنا. سنقوم بمراجعة طلبك والتواصل معك في حال ترشيحك لأي دور مناسب. بالتوفيق!")
            del user_states[phone]  # مسح الرقم من الذاكرة المؤقتة لإنهاء المحادثة بنجاح

    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    # تشغيل محلي في حال أردت تجربته على جهازك لاحقاً
    app.run(port=5000)

