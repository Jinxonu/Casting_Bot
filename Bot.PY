from flask import Flask, request, jsonify
import requests
from pyngrok import ngrok

app = Flask(__name__)

# ==================== إعدادات الربط المهمة ====================
# 1. ضع هنا كود الـ Authtoken الذي نسخته من موقع ngrok
NGROK_AUTH_TOKEN = "ضع_هنا_كود_الـ_AUTHTOKEN_الخاص_بك"

# 2. بيانات الـ API الخاص بالواتساب (تأكد من تعديلها ببيانات حسابك في Ultramsg أو الخدمة التي تستخدمها)
API_URL = "https://ultramsg.com"
TOKEN = "your_secret_token"
# ============================================================

# قاعدة بيانات مؤقتة لتخزين "حالة" كل رقم وبياناته
user_states = {}

def send_whatsapp_message(to_phone, text):
    payload = {"token": TOKEN, "to": to_phone, "body": text}
    try:
        requests.post(API_URL, data=payload)
    except Exception as e:
        print(f"خطأ في إرسال الرسالة: {e}")

@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    data = request.json
    if not data:
        return jsonify({"status": "no_data"})
        
    phone = data.get("from") # رقم مرسل الرسالة
    message = data.get("body", "").strip() # نص الرسالة المستلمة

    if not phone or not message:
        return jsonify({"status": "ignored"})

    # 1. إذا كان المستخدم جديداً ولم يحدد هويته بعد
    if phone not in user_states:
        user_states[phone] = {"stage": "welcome", "type": None}
        welcome_text = (
            "مرحباً بك في وكالة المواهب! 🌟\n\n"
            "يرجى تحديد هويتك لتوجيهك بشكل صحيح:\n"
            "1️⃣ - أنا ممثل/موهبة أرغب بالانضمام للوكالة.\n"
            "2️⃣ - أنا عميل / شركة إنتاج وأبحث عن مواهب."
        )
        send_whatsapp_message(phone, welcome_text)
        return jsonify({"status": "success"})

    current_stage = user_states[phone]["stage"]

    # 2. مسار التوجيه بناءً على الاختيار الأول
    if current_stage == "welcome":
        if message == "1":
            user_states[phone]["stage"] = "ask_name"
            user_states[phone]["type"] = "talent"
            send_whatsapp_message(phone, "أهلاً بك معنا! لنبدأ خطوات التسجيل.\nالرجاء كتابة اسمك الثلاثي:")
        elif message == "2":
            user_states[phone]["stage"] = "client_handling"
            user_states[phone]["type"] = "client"
            send_whatsapp_message(phone, "أهلاً وسهلاً بك يا فندم. يرجى كتابة اسم الشركة ونوع المشروع (مسلسل، إعلان، فيلم) وسيقوم أحد عملائنا بالتواصل معك فوراً.")
        else:
            send_whatsapp_message(phone, "عذراً، يرجى اختيار الرقم 1 أو 2 فقط.")
        return jsonify({"status": "success"})

    # 3. استكمال مسار الموهبة (استقبال البيانات بالتوالي)
    if user_states[phone].get("type") == "talent":
        if current_stage == "ask_name":
            user_states[phone]["name"] = message
            user_states[phone]["stage"] = "ask_age"
            send_whatsapp_message(phone, f"تشرفنا يا {message}. كم عمرك؟")
            
        elif current_stage == "ask_age":
            user_states[phone]["age"] = message
            user_states[phone]["stage"] = "ask_photos"
            send_whatsapp_message(phone, "ممتاز. الرجاء إرسال صور حديثة لك أو روابط صور واضحة:")
            
        elif current_stage == "ask_photos":
            user_states[phone]["photos"] = message 
            user_states[phone]["stage"] = "ask_showreel"
            send_whatsapp_message(phone, "أخيراً، يرجى إرسال رابط الـ Showreel الخاص بك (يوتيوب، قوقل درايف، إلخ):")
            
        elif current_stage == "ask_showreel":
            user_states[phone]["showreel"] = message
            
            # حفظ البيانات في الـ Terminal كإثبات نجاح
            print(f"🎉 تم استقبال موهبة جديدة: {user_states[phone]['name']} - العمر: {user_states[phone]['age']}")
            
            send_whatsapp_message(phone, "شكراً لك! تم تسجيل بياناتك بنجاح في وكالتنا. سنقوم بمراجعة طلبك والتواصل معك في حال ترشيحك لأي دور مناسب. بالتوفيق!")
            del user_states[phone]

    return jsonify({"status": "success"})

if __name__ == "__main__":
    # تفعيل مفتاح الأمان لـ ngrok
    ngrok.set_auth_token(NGROK_AUTH_TOKEN)
    
    # فتح النفق التلقائي عبر الإنترنت لمنفذ السيرفر 5000
    public_url = ngrok.connect(5000).public_url
    print("\n" + "="*50)
    print(f"🔗 رابط الـ Webhook الخاص بك هو:\n{public_url}/webhook")
    print("="*50 + "\n")
    
    app.run(port=5000, use_reloader=False)
