from flask import Flask, request, jsonify
import os
import requests
import datetime
from supabase_client import supabase

app = Flask(__name__)

# Doctor details
doctors = [
    {"name": "डा. किशोर कुमार पौडेल", "degree": "MBBS, DMRD (CMC VELLORE)", "speciality": "वरिष्ठ रेडियोलोजिष्ट", "nmc": "13362", "time": "प्रत्येक दिन विहान ८:०० बजे र बेलुका ४:०० बजे देखि"},
    {"name": "डा. बरुण अग्रवाल", "degree": "MBBS, MD (BPKIHS)", "speciality": "वरिष्ठ नवजात शिशु तथा बाल रोग विशेषज्ञ", "nmc": "15375", "time": "प्रत्येक दिन विहान २:३० बजे देखि"},
    {"name": "डा. शिवेस चौधरी", "degree": "MBBS, MS (BPKIHS)", "speciality": "वरिष्ठ स्त्री तथा प्रसूति रोग विशेषज्ञ", "nmc": "16367", "time": "प्रत्येक शनिवार विहान १२:०० बजे देखि"},
    {"name": "डा. दिलिप गुप्ता", "degree": "MBBS (BPKIHS), MD (BPKIHS)", "speciality": "वरिष्ठ फिजिसियन", "nmc": "17431", "time": "प्रत्येक शनिवार विहान २ बजे र मंगलवार विहान ८ बजे"},
    {"name": "डा. रितेश थपलिया", "degree": "MBBS MS (BPKIHS)", "speciality": "वरिष्ठ हाड जोर्नी तथा नसारोग विशेषज्ञ", "nmc": "14215", "time": "प्रत्येक शनिवार र मंगलवार विहान ८:०० बजे"},
    {"name": "डा. शशांकराज पोखरेल", "degree": "MBBS, MD (BPKIHS)", "speciality": "वरिष्ठ टाउको, नसारोग तथा मानसिक रोग विशेषज्ञ", "nmc": "14450", "time": "प्रत्येक शनिवार विहान १:३० बजे देखि"},
    {"name": "डा. पोषण त्रिपाठी", "degree": "MBBS (IOM) MDGP (BPKIHS)", "speciality": "वरिष्ठ फेमिली फिजिसियन", "nmc": "4783", "time": "दैनिक बेलुका ५ बजे देखि"},
    {"name": "डा. निस्तुक बराल", "degree": "MBBS. MD (KU)", "speciality": "वरिष्ठ छाला, कुष्ठ, यौन तथा सौन्दर्य विशेषज्ञ", "nmc": "16919", "time": "प्रत्येक शुक्रवार ३:०० बजे देखि"},
    {"name": "डा. शिव भूषण पण्डित", "degree": "MBBS(TU), MS(KU)", "speciality": "वरिष्ठ नाक, कान, घाँटी रोग विशेषज्ञ", "nmc": "16947", "time": "प्रत्येक शनिवार विहान २:३० बजे देखि"},
    {"name": "डा. गीरेन्द्र यादव", "degree": "MBBS, BPKIHS DHARAN", "speciality": "मेडिकल अफिसर", "nmc": "32439", "time": "२४ सै घण्टा सेवा"}
]

# Lab test details
lab_tests = {
    "CBC": 300,
    "Lipid Profile": 800,
    "Blood Sugar (Fasting)": 100,
    "Thyroid Function Test": 1000,
    "RFT किड्नीको जाँच (Kidney Function)": 900,
    "LFT कालेजों जाँच": 900,
    "USG Abdomen Pelvis": 1000,
    "Other Test": "Please request the test you want. Prices are based according to market."
}

def auto_reply(message):
    message = message.lower()

    if "doctor" in message or "appointment" in message:
        reply = "📅 Doctor Appointment Schedule:\n"
        for doc in doctors:
            reply += f"➡️ {doc['name']} ({doc['speciality']}) - {doc['time']}\n"
        reply += "\nकृपया कुन डाक्टरसँग appointment चाहनुहुन्छ भन्नुहोस्।"
        return reply

    elif "lab" in message or "test" in message:
        reply = "🧪 Available Lab Tests and Prices:\n"
        for test, price in lab_tests.items():
            reply += f"- {test}: Rs. {price}\n" if isinstance(price, int) else f"- {test}: {price}\n"
        reply += "\nकृपया कुन test को लागि appointment चाहनुहुन्छ भन्नुहोस्।"
        return reply

    elif "book" in message:
        return "📋 कृपया आफ्नो नाम र फोन नम्बर पठाउनुहोस् (format: Name, Phone) appointment बुक गर्न।"

    elif "," in message:
        try:
            name, phone = [x.strip() for x in message.split(",")]
            supabase.table("appointments").insert({
                "name": name,
                "phone": phone,
                "created_at": datetime.datetime.now().isoformat()
            }).execute()
            return f"✅ Appointment booked successfully!\n👤 Name: {name}\n📞 Phone: {phone}"
        except Exception as e:
            print(f"Booking Error: {e}")
            return "❌ Booking failed. Please try again."

    elif "hello" in message or "hi" in message:
        return "👋 Welcome to Trihari Polyclinic & Diagnostic Centre!\nYou can ask about Doctors, Appointments, or Lab Tests."

    else:
        return "Sorry, I didn't understand. You can ask for 'doctor', 'appointment', 'lab test', or 'book'."

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    # WhatsApp verification (GET request)
    if request.method == 'GET':
        verify_token = os.getenv('WHATSAPP_VERIFY_TOKEN')
        if request.args.get('hub.verify_token') == verify_token:
            return request.args.get('hub.challenge')
        return "Invalid verification token"

    # Handle incoming messages (POST request)
    data = request.json
    
    # WhatsApp format
    if data.get('object') == 'whatsapp_business_account':
        try:
            message = data['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']
            sender = data['entry'][0]['changes'][0]['value']['contacts'][0]['wa_id']
            reply = auto_reply(message)
            
            # Send reply via Meta API
            headers = {
                'Authorization': f"Bearer {os.getenv('WHATSAPP_TOKEN')}",
                'Content-Type': 'application/json'
            }
            payload = {
                "messaging_product": "whatsapp",
                "to": sender,
                "text": {"body": reply}
            }
            response = requests.post(
                f"https://graph.facebook.com/v18.0/{os.getenv('WHATSAPP_PHONE_ID')}/messages",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return jsonify({"status": "success"}), 200
            
        except Exception as e:
            print(f"WhatsApp Error: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    # General API format (for testing)
    elif request.is_json and 'message' in request.json:
        bot_reply = auto_reply(request.json['message'])
        return jsonify({"reply": bot_reply})
    
    return jsonify({"status": "unhandled request"}), 400

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
