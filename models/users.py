from pymongo import MongoClient
client = MongoClient("mongodb://127.0.0.1:27017/")
db = client["tyche_app"]
users_collection = db["users"]

def checkUserExists(email):
    user = users_collection.find_one({"email": {"$regex": email, "$options": "i"}}) # check if user exist
    if not user:
        return False
    else:
        return True
def saveUser(user_json):
    users_collection.insert_one(user_json)

def getAllUsers(where):
    users = users_collection.find(where)
    return users
async def getUserInfo(where):
    user = users_collection.find_one(where,{"_id": 0})
    return user

def getUserDataForMatching(email):
    user = users_collection.find_one({"email": email}, {"_id": False})
    return user
    
def getAllUsersDataForMatching(email):
    users = users_collection.find({"email": {"$ne": email}}, {"_id": False})
    return users
def updateUserData(email, data):
    users_collection.update_one({'email': email}, {'$set':data})

def insertAnswers(answer_info):
    user = users_collection.find_one({"email": answer_info['email']}, {"_id": False})
    if "questions" in user:
        questions = user['questions']
    else:
        questions = []
    questions.append({'question': answer_info['question'], 'message': answer_info['message']})
    users_collection.update_one({"email": answer_info['email']}, {"$set": {'questions': questions}})
