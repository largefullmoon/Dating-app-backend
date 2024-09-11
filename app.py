from flask import Flask
from pymongo import MongoClient
from flask import Flask, request, jsonify, send_file, Response, stream_with_context, send_from_directory
from flask_cors import CORS
import hashlib
from twilio.rest import Client
import random
from dotenv import load_dotenv
import os
from models.users import * 
from models.photos import * 
from models.chats import * 
from services.twilio import * 
from flask_socketio import SocketIO, send

account_sid = os.getenv('account_sid')
auth_token = os.getenv('auth_token')
from_number = os.getenv('from_number')

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Adjust the origin to your React app's URL
cors = CORS(app, resources={r"/*": {"origins": "*"}}, methods=["GET", "POST", "OPTIONS"])
app.app_context().push()

socketio = SocketIO(app, cors_allowed_origins='*')

client = MongoClient("mongodb://127.0.0.1:27017/")
db = client["mobileapp"]
users_collection = db["users"]
chats_collection = db["chats"]

@app.route("/", methods=["get"])
def welcome():
    return "welcome"
@app.route("/registerUser", methods=["POST"])
def registerUser():
    new_user = request.get_json()
    isexists = checkUserExists(new_user["email"])
    if isexists:
        return "user already exists", 404
    try:
        verifyCode = random.randint(10000, 99999)
        message_body = 'Hello, This is your verification code for Tyche: '+ str(verifyCode)
        # sms_sid = send_sms(phoneNumner, message_body)
        user_json = {
            'email': new_user['email'],
            'firstName': new_user['firstName'],
            'lastName': new_user['lastName'],
            'fullName': new_user['firstName']+" "+new_user['lastName'],
            'birthday': new_user['birthday'],
            'sex': new_user['sex'],
            'birthdayPresent': new_user['birthdayPresent'],
            'phoneNumber': new_user['phoneNumner'],
            'verifyCode': verifyCode
        }
        saveUser(user_json)
        print("success")
        return "register successed", 200
    except Exception as e:
        print(e)
        return "register failed", 404
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

@app.route("/getPhoto/<filename>", methods=["GET"])
def getPhoto(filename):
    # Make sure the directory exists
    if not os.path.exists('photos'):
        return 'Directory not found', 404

    # Check if the file exists in the directory
    if not os.path.exists(os.path.join('photos', filename)):
        return 'File not found', 404

    # Send the file from the directory
    return send_from_directory('photos', filename)

@app.route("/getPhotoList", methods=["POST"])
def getPhotoList():
    user_info = request.get_json()
    user = getUser({"email" : user_info['email']})
    if 'photos' in user:
        photos = user['photos']
    else:
        photos = ["default.png","default.png","default.png","default.png","default.png","default.png"]
    return jsonify({'status': 'success', 'photos': photos}), 200
@app.route("/uploadPhoto", methods=["POST"])
def uploadPhoto():
    if 'file' not in request.files:
        print("No file part")
        return 'No file part', 400
    file = request.files['file']
    
    if file.filename == '':
        print("No selected file")
        return 'No selected file', 400

    # Ensure the 'photos' directory exists
    if not os.path.exists('photos'):
        os.makedirs('photos')
    try:
        # Save the file to the specified location
        params = request.form
        user = getUser({"email": params["email"]})
        if "photos" in user:
            photos = user['photos']
        else:
            photos = []
        file_root, file_extension = os.path.splitext(file.filename)
        filename = (len(photos)+1)+file_extension
        print(filename)
        file.save(os.path.join('photos', filename))
        print("File uploaded successfully")
        photos.append(len(photos)+1)
        updateUserData(params["email"], {"photo": photos})
    except:
        print("File upload failed")
    return 'File uploaded successfully', 200

@app.route("/verifyPhoneNumber", methods=["POST"])
def verifyPhoneNumber():
    verifyInfo = request.get_json()
    user = getUser({"email":verifyInfo["email"]})
    if user['verifyCode'] == verifyInfo['code']:
        updateUserData(verifyInfo['email'], {'verified':True})
        return jsonify({'message': 'success'}), 200
    else:
        return jsonify({'message': 'failed'}), 200
        

@app.route("/selectPlan", methods=["POST"])
def selectPlan():
    plan_info = request.get_json()
    user = getUser({"email":plan_info["email"]})
    if user:
        updateUserData(plan_info['email'], {'plan':plan_info['plan']})
    return jsonify({'status': 'success', 'plan': plan_info['plan']}), 200
@app.route("/chatwithAI", methods=["POST"])
def chatwithAI():
    answer_info = request.get_json()
    insertAnswers(answer_info)
    return jsonify({'status': 'success'}), 200

@socketio.on('chatwithUser')
def handle_message(chat_info):
    insertChat(chat_info)
    send(chat_info, broadcast=True)
    
@app.route("/chatwithUser", methods=["POST"])
def chatwithUser():
    chat_info = request.get_json()
    insertChat(chat_info)
    return jsonify({'status': 'success'}), 200
        
@app.route("/getChatUsers", methods=["POST"])
def getChatUsers():
    user_info = request.get_json()
    users = getAllUsers({})
    results = []
    for user in users:
        if user_info['email'] == user['email']:
            continue
        result = {}
        result['name'] = user['fullName']
        if 'photo' in user:
            result['photo'] = user['photo']
        else:
            result['photo'] = 'default.png'
        result['lastMessage'] = getLastMessage(user_info['email'], user['email'])
        results.append(result)
    print(results)
    return jsonify({'message': 'success', 'data': results}), 200

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

def get_openai_response(user_input):
    try:
        stream = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": user_input}],
            stream=True,
        )
        full_response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                full_response += content
        return full_response

    except Exception as e:
        return e

def getMatchScore(fuser, suser):
    query = """
    Please provide a matching score between there 2 arrays
    1. """+fuser['questions']+"""
    2. """+suser['questions']+"""
    Note: return only the matching score without % sign
    """
    score = get_openai_response(query)
    return score

@app.route("/getSuggestMatchs", methods=["POST"])
def getSuggestMatchs():
    params = request.get_json()
    fuser = getUserDataForMatching(params['email'])
    userDatas =  getAllUsersDataForMatching()
    for suser in userDatas:
        score = getMatchScore(fuser, suser)
    return "success"