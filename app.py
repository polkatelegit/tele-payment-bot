from flask import Flask,request,jsonify,abort,render_template
import hashlib
import json
import hmac
import subprocess
import os
import signal
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore



app= Flask(__name__)
global script_process, script_pid
WEBHOOK_SECRET = "6851492f-9db5-4cef-83b3-6f207d5e46d4"


cred = credentials.Certificate('firebase_key.json')
firebase_admin.initialize_app(cred)
db = firestore.client()
                              

@app.route('/')
def index():
    return ("Welcome to the world!!!")

@app.route("/start")
def start():
    global script_process,script_pid
    script_process=subprocess.Popen(["python", "bot.py"])
    script_pid = script_process.pid
    return "Bot started!"

@app.route("/stop")
def stop():
    global script_process,script_pid
    try:
        os.kill(script_pid,signal.SIGTERM)
        return "Bot stopped!"
    except Exception as e:
        return "Bot is already stopped."
    
@app.route('/webhook',methods=['POST'])
def handle_webhook():

    payments_data ={}

    signature = request.headers.get('X-CC-Webhook-Signature')
    if not signature:
        abort(400,'No signature provided')

    payload =request.get_data()
    computed_signature = hmac.new(bytes(WEBHOOK_SECRET,'utf-8'),payload,hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, computed_signature):
        abort(401, 'Invalid Signature')

    try:

        read_db(payments_data,'payments_data')

        payload = request.get_json()
        metadata = payload['event']['data']['metadata']
        charge_id = payload['event']['data']['id']
        charge_type = payload['event']['type']
        
        if charge_type == "charge:confirmed":
            userID = metadata['user_id']
            if userID in payments_data:
                if charge_id in payments_data[userID]:
                    for elem in payload['event']['data']['timeline']:
                        if "payment" in elem:
                            if elem['status'] =="COMPLETED":
                                payments_data[userID][charge_id]['status'] = "confirmed"
                                
        elif charge_type == "charge:pending":
            userID = metadata['user_id']
            if userID in payments_data:
                if charge_id in payments_data[userID]:
                    payments_data[userID][charge_id]['status'] = "pending"
            
        elif charge_type == "charge:failed":
            userID = metadata['user_id']
            if charge_id in payments_data[userID]:
                for elem in payload['event']['data']['timeline']:
                    if 'payment' in elem:
                        if elem['status'] == "UNRESOLVED":
                            if 'context' in elem:
                                if elem['context'] == "OVERPAID":
                                    payments_data[userID][charge_id]['status'] = "confirmed"
                                elif elem['context'] == "UNDERPAID":
                                    actual_amount = elem['payment']['value']['amount']
                                    expected_amount = payments_data[userID][charge_id]['amount']
                                    amount_diff = float(expected_amount)-float(actual_amount)
                                    current_exchnage_rate = float(payload['event']['data']['exchange_rates']['LTC-USD'])
                                    usd_value = amount_diff*current_exchnage_rate

                                    if usd_value < 1:
                                        payments_data[userID][charge_id]['status'] = "confirmed"
                                    else:
                                        payments_data[userID][charge_id]['status'] = "failed"
                                        payments_data[userID][charge_id]['sub_status'] = "underpaid"
                      
                    else:
                        if elem['status'] == "EXPIRED":
                            payments_data[userID][charge_id]['status'] = "failed"
                            payments_data[userID][charge_id]['sub_status'] = "expired"

    except Exception as e:
        abort(400,'Failed to parse JSON payload: {}'.format(e))
    
    write_to_db(payments_data,'payments_data')
    return jsonify({'status': 'success'})



def write_to_db(dictonary_name,dict_name):
    try:
        for key,value in dictonary_name.items():
            doc_ref = db.collection(dict_name).document(key)
            doc_ref.set(value)

    except Exception as e:
        print(f"Error in exception {e}")

def read_db(wDictonary,dict_name):
    data_ref = db.collection(dict_name)
    data_docs = data_ref.get()
    for doc in data_docs:
        wDictonary[doc.id] = doc.to_dict()


if __name__ == "__main__":
    app.run(debug=False,host='0.0.0.0')