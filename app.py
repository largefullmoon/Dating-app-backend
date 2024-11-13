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
db = client["tyche_app"]
users_collection = db["users"]
chats_collection = db["chats"]

import logging, math
# logging.basicConfig(filename='actions.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
@app.route("/", methods=["get"])
def welcome():
    return "welcome"
@app.route("/phone", methods=["post"])
def phone():
    verifyCode = random.randint(10000, 99999)
    message_body = 'Hello, This is your verification code for Tyche: '+ str(verifyCode)
    data = request.get_json()
    number = data['number']
    sms_sid = send_sms(number, message_body)
    return {"data" : "welcome"}
@app.route("/webhook", methods=["post"])
def webhook():
    data = request.get_json()
    print(data)
    return {"data" : "webHook is running"}
@app.route("/registerUser", methods=["POST"])
def registerUser():
    new_user = request.get_json()
    isexists = checkUserExists(new_user["email"])
    if isexists:
        return "user already exists", 404
    try:
        verifyCode = random.randint(10000, 99999)
        message_body = 'Hello, This is your verification code for Tyche: '+ str(verifyCode)
        user_json = {
            'email': new_user['email'],
            'firstName': new_user['firstName'],
            'lastName': new_user['lastName'],
            'fullName': new_user['firstName']+" "+new_user['lastName'],
            'birthday': new_user['birthday'],
            'sex': new_user['sex'],
            'birthdayPresent': new_user['birthdayPresent'],
            'phoneNumber': new_user['phoneNumber'],
            'verifyCode': verifyCode,
            'photo' : ["default"]
        }
        saveUser(user_json)
        sms_sid = send_sms(new_user['phoneNumber'], message_body)
        print("success")
        return "register successed", 200
    except Exception as e:
        print(e)
        return "register failed", 404
@app.route("/verifyCode", methods=["POST"])
async def verifyCode():
    params = request.get_json()
    user = await getUserInfo({"email":params["email"], "verifyCode": params["verifyCode"]})
    if user:
        users_collection.update_one({'email': params["email"]}, {'$set':{'isVerified':True}})

@app.route("/agreeTerms", methods=["POST"])
async def agreeTerms():
    user_info = request.get_json()
    try:
        user = await getUserInfo({"email":user_info["email"]}) # check if user exist
        if user:
            users_collection.update_one({'email': user_info["email"]}, {'$set':{'termsAgreed':True}})
        print("success")
        return "register successed", 200
    except Exception as e:
        print(e)
        return "register failed", 404
    
@app.route("/getPhoto/<filename>", methods=["GET"])
def getPhoto(filename):
    # Make sure the directory exists
    if not os.path.exists('photos'):
        print('Directory not found')
        return 'Directory not found', 404

    # Check if the file exists in the directory
    if not os.path.exists(os.path.join('photos', filename)):
        print('File not found')
        return 'File not found', 404

    # Send the file from the directory
    return send_from_directory('photos', filename)

@app.route("/getPhotoList", methods=["POST"])
async def getPhotoList():
    user_info = request.get_json()
    user = await getUserInfo({"email" : user_info['email']})
    if user and 'photo' in user:
        photos = user['photo']
    else:
        photos = ["default.png"]
    return jsonify({'status': 'success', 'photos': photos}), 200
@app.route("/uploadPhoto", methods=["POST"])
async def uploadPhoto():
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
        print(params)
        user = await getUserInfo({"email": params["email"]})
        if "photo" in user:
            photos = user['photo']
            if photos[0] == 'default':
                photos = []
        else:
            photos = []
        file_root, file_extension = os.path.splitext(file.filename)
        filename = params["email"]+"-"+params["number"]+'.png'
        file.save(os.path.join('photos', filename))
        photos = [params["number"] if x == params["number"] else x for x in photos]
        if params["number"] not in photos:
            photos.append(params["number"])
        updateUserData(params["email"], {"photo": photos})
    except Exception as e:
        print(e)
    return 'File uploaded successfully', 200
@app.route("/updatePhotoList", methods=["POST"])
async def updatePhotoList():
    params = request.form
    updatedphotolist = params['data']
    for photo in updatedphotolist:
        filename = params["email"]+"-"+photo["from"]+'.png'
        original_path = os.path.join('photos', filename)
        new_filename = params["email"]+"-"+photo["to"]+'.png'
        new_path = os.path.join('photos', new_filename)
        os.rename(original_path, new_path)
    return 'Updated successfully', 200    
@app.route("/verifyPhoneNumber", methods=["POST"])
async def verifyPhoneNumber():
    verifyInfo = request.get_json()
    user = await getUserInfo({"email":verifyInfo["email"]})
    print(user)
    print(verifyInfo)
    if str(user['verifyCode']) == verifyInfo['code']:
        updateUserData(verifyInfo['email'], {'verified':True})
        print("success")
        return jsonify({'message': 'success'}), 200
    else:
        print("failed")
        return jsonify({'message': 'failed'}), 400

@app.route("/selectPlan", methods=["POST"])
async def selectPlan():
    plan_info = request.get_json()
    user = await getUserInfo({"email":plan_info["email"]})
    if user:
        updateUserData(plan_info['email'], {'plan':plan_info['plan']})
    return jsonify({'status': 'success', 'plan': plan_info['plan']}), 200
@app.route("/answerQuestion", methods=["POST"])
def answerQuestion():
    answer_info = request.get_json()
    insertAnswers(answer_info)
    return jsonify({'status': 'success'}), 200
@app.route("/getChatList", methods=["POST"])
async def getChatList():
    params = request.get_json()
    chatList = await getChats(params)
    return jsonify({'data': chatList}), 200

@app.route("/setChatStatus", methods=["POST"])
async def setChatStatus():
    params = request.get_json()
    chatList = await readChatList(params)
    return jsonify({'status': 'success'}), 200

@socketio.on('chatwithUser')
def handle_message(chat_info):
    print(chat_info)
    insertChat(chat_info)
    send(chat_info, broadcast=True)
        
@app.route("/getChatUsers", methods=["POST"])
async def getChatUsers():
    user_info = request.get_json()
    users = getAllUsers({})
    results = []
    for user in users:
        if user_info['email'] == user['email']:
            continue
        result = {}
        result['name'] = user['fullName']
        result['email'] = user['email']
        result['birthday'] = user['birthday']
        if 'photo' in user:
            result['photo'] = user['photo']
        else:
            result['photo'] = 'default.png'
        lastChat = await getLastMessage(user_info['email'], user['email'])
        result['lastMessage'] = lastChat['message']
        result['read'] = lastChat['read']
        results.append(result)
    print(results)
    return jsonify({'message': 'success', 'data': results}), 200

@app.route("/getUser", methods=["POST"])
async def getUser():
    try:
        params = request.get_json()
        print(params, "params")
        user = await getUserInfo({'email':params['email']})
        return jsonify({'message': 'success', 'data': user}), 200
    except Exception as e:
        print(e)

@app.route("/getChatHistory", methods=["POST"])
def getChatHistory():
    user_info = request.get_json()
    chats = chats_collection.find_one({"from-email":user_info["from-email"], "to-email":user_info["to-email"]}) # check if user exist
    return jsonify({'message': 'success', 'data': [chat for chat in chats]}), 200

@app.route("/signInApple", methods=["POST"])
def signInApple():
    return "welcome to our app" 

@app.route("/getUserPhoto", methods=["POST"])
async def getUserPhoto():
    params = request.get_json()
    print(params)
    user = await getUserInfo({"email":params["email"]})
    if 'photo' in user:
        photo = user['photo'][0]
    else:
        photo = 'default'
    return jsonify({'message': 'success', 'photo': photo}), 200
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