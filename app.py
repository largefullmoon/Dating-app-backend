from flask import Flask
from pymongo import MongoClient
from flask import Flask, request, jsonify, send_file, Response, stream_with_context
from flask_cors import CORS
import hashlib
from twilio.rest import Client
import random


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Adjust the origin to your React app's URL
cors = CORS(app, resources={r"/*": {"origins": "*"}}, methods=["GET", "POST", "OPTIONS"])
app.app_context().push()

client = MongoClient("mongodb://127.0.0.1:27017/")
db = client["Tyche"]
users_collection = db["users"]
chats_collection = db["chats"]


@app.route("/registerUser", methods=["POST"])
def registerUser():
    new_user = request.get_json()
    user = users_collection.find_one({"email": {"$regex": new_user["email"], "$options": "i"}}) # check if user exist
    if not user:
        try:
            verifyCode = random.randint(10000, 99999)
            message_body = 'Hello, This is your verification code for Tyche: '+ verifyCode
            sms_sid = send_sms(new_user["phoneNumber"], message_body)
            user_id = str(uuid4())
            new_user["password"] = hashlib.sha256(new_user["password"].encode("utf-8")).hexdigest() # encrpt password
            user_json = {
                "id": user_id,
                'email': new_user['email'],
                'firstName': new_user['firstName'],
                'lastName': new_user['lastName'],
                'fullName': new_user['firstName']+" "+new_user['lastName'],
                'birthday': new_user['birthday'],
                'sex': new_user['sex'],
                'birthdayPresents ': new_user['birthdayPresents'],
                'phoneNumber': new_user['phoneNumber'],
                'verifyCode': verifyCode
            }
            users_collection.insert_one(user_json)
            print(f"Message sent successfully! SID: {sms_sid}")
        except Exception as e:
            print(f"Failed to send message: {e}")
def send_sms(phone_number, message_body):
    message = client.messages.create(
        body=message_body,        # The body of the SMS message
        from_=from_number,        # Your Twilio number
        to=phone_number           # The recipient's phone number
    )
    return message.sid  # Return the message SID
@app.route("/verifyCode", methods=["POST"])
def verifyCode():
    params = request.get_json()
    user = users_collection.find_one({"email":new_user["email"], "verifyCode": params["verifyCode"]}) # check if user exist
    if user:
        users_collection.update_one({'email': params["email"]}, {'$set':{'isVerified':True}})
        
        
@app.route("/agreeTerms", methods=["POST"])
def agreeTerms():
    user_info = request.get_json()
    user = users_collection.find_one({"email":new_user["email"]}) # check if user exist
    if user:
        users_collection.update_one({'email': user_info["email"]}, {'$set':{'termsAgreed':True}})
        
        
@app.route("/uploadPhoto", methods=["POST"])
def uploadPhoto():
    user_info = request.get_json()
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    
    if file.filename == '':
        return 'No selected file', 400

    file.save(f"/photos/{file.filename}")
    return 'File uploaded successfully', 200

@app.route("/selectPlan", methods=["POST"])
def selectPlan():
    plan_info = request.get_json()
    user = users_collection.find_one({"email":plan_info["email"]}) # check if user exist
    if user:
        users_collection.update_one({'email': plan_info["email"]}, {'$set':{'plan':plan_info['plan']}})
        
@app.route("/getChatUsers", methods=["POST"])
def getChatUsers():
    users = users_collection.find({'isVerified': True, 'termsAgreed': True}) # check if user exist
    return jsonify({'message': 'success', 'data': [user for user in users]}), 200