pip install firebase-admin

import firebase_admin
from firebase_admin import credentials, firestore
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
import threading



app= Flask(__name__)
# global script_process, script_pid
WEBHOOK_SECRET = "6851492f-9db5-4cef-83b3-6f207d5e46d4"

lock = threading.Lock()

global script_process,script_pid
script_process= None
script_pid =None


cred = credentials.Certificate('firebase_key.json')
firebase_admin.initialize_app(cred)
db = firestore.client()



@app.route('/')
def index():
    return ("Welcome to the world!!!")

@app.route("/start")
def start():
    global script_process,script_pid
    if script_process:
        return "Bot is already running!!!"
    else:
        script_process=subprocess.Popen(["python", "bot.py"])
        script_pid = script_process.pid
        return "Bot started!"

@app.route("/stop")
def stop():
    global script_process,script_pid
    try:
        os.kill(script_pid,signal.SIGTERM)
        script_process =None
        script_pid =None

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
        lock.acquire()
        read_db(payments_data,'payments_data')

        payload = request.get_json()
        metadata = payload['event']['data']['metadata']
        charge_type = payload['event']['type']
        userID = metadata['user_id']

        if not str(userID) in payments_data['payments']:
            payments_data['payments'][str(userID)] = {}
            payments_data['payments'][str(userID)]['balance'] = 0

        ltc_exchange_rate = float(payload['event']['data']['exchange_rates']['LTC-USD'])
        
        
        if charge_type == "charge:confirmed":
            if userID in payments_data:
                for elem in payload['event']['data']['timeline']:
                        if "payment" in elem:
                            if elem['status'] =="COMPLETED":
                                coin_amount = float(elem['payment']['value']['amount'])
                                usd_value  = round(coin_amount*ltc_exchange_rate,2)
                                payments_data['payments'][userID]['balance'] =payments_data['payments'][userID]['balance']+ usd_value

                                
        elif charge_type == "charge:pending":
            userID = metadata['user_id']
            if userID in payments_data:
                return
            
        elif charge_type == "charge:failed":
            userID = metadata['user_id']
            for elem in payload['event']['data']['timeline']:
                if 'payment' in elem:
                    if elem['status'] == "UNRESOLVED":
                        if 'context' in elem:
                            if elem['context'] == "OVERPAID" or elem['context'] == "UNDERPAID":
                                coin_amount = float(elem['payment']['value']['amount'])
                                usd_value  = round(coin_amount*ltc_exchange_rate,2)
                                payments_data['payments'][userID]['balance'] =payments_data['payments'][userID]['balance']+ usd_value

        write_to_db(payments_data,'payments_data')

    except Exception as e:
        abort(400,'Failed to parse JSON payload: {}'.format(e))
    
    finally:
        lock.release() 
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
