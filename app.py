from flask import Flask
from pymongo import MongoClient
from flask import Flask, request, jsonify, send_file, Response, stream_with_context
from flask_cors import CORS
import hashlib
from twilio.rest import Client
import random
from dotenv import load_dotenv
import os
from models.users import * 
from services.twilio import * 

account_sid = os.getenv('account_sid')
auth_token = os.getenv('auth_token')
from_number = os.getenv('from_number')

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Adjust the origin to your React app's URL
cors = CORS(app, resources={r"/*": {"origins": "*"}}, methods=["GET", "POST", "OPTIONS"])
app.app_context().push()

client = MongoClient("mongodb://127.0.0.1:27017/")
db = client["Tyche"]
users_collection = db["users"]
chats_collection = db["chats"]

@app.route("/", methods=["get"])
def welcome():
    return "welcome"
@app.route("/registerUser", methods=["POST"])
def registerUser():
    new_user = request.get_json()
    isexists = checkUserExists(new_user["email"])
    if isexists == False:
        try:
            verifyCode = random.randint(10000, 99999)
            message_body = 'Hello, This is your verification code for Tyche: '+ verifyCode
            sms_sid = send_sms(new_user["phoneNumber"], message_body)
            new_user["password"] = hashlib.sha256(new_user["password"].encode("utf-8")).hexdigest() # encrpt password
            user_json = {
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
            saveUser(user_json)
            return "success"
        except Exception as e:
            return "failure"
    else:
        return "already exist"
@app.route("/verifyCode", methods=["POST"])
def verifyCode():
    params = request.get_json()
    user = getUser({"email":params["email"], "verifyCode": params["verifyCode"]})
    if user:
        users_collection.update_one({'email': params["email"]}, {'$set':{'isVerified':True}})

@app.route("/agreeTerms", methods=["POST"])
def agreeTerms():
    user_info = request.get_json()
    user = getUser({"email":user_info["email"]}) # check if user exist
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
    user = getUser({"email":plan_info["email"]})
    if user:
        users_collection.update_one({'email': plan_info["email"]}, {'$set':{'plan':plan_info['plan']}})
        
@app.route("/getChatUsers", methods=["POST"])
def getChatUsers():
    users = getAllUsers({'isVerified': True, 'termsAgreed': True})
    return jsonify({'message': 'success', 'data': [user for user in users]}), 200

@app.route("/getChatHistory", methods=["POST"])
def getChatHistory():
    user_info = request.get_json()
    chats = chats_collection.find_one({"from-email":user_info["from-email"], "to-email":user_info["to-email"]}) # check if user exist
    return jsonify({'message': 'success', 'data': [chat for chat in chats]}), 200


app.route("/getAnswer", methods=["POST"])
def getAnswer():
    return "welcome chat"

@app.route("/signInApple", methods=["POST"])
def signInApple():
    return "welcome to our app" 
