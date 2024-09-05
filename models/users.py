from pymongo import MongoClient
client = MongoClient("mongodb://127.0.0.1:27017/")
db = client["Tyche"]
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
def getUser(where):
    user = users_collection.find_one({'isVerified': True, 'termsAgreed': True})
    return user

def getUserDataForMatching(email):
    user = users_collection.find_one({"email": email}, {"_id": False})
    return user
    
def getAllUsersDataForMatching(email):
    users = users_collection.find({"email": {"$ne": email}}, {"_id": False})
    return users

def insertAnswers(answer_info):
    user = users_collection.find_one({"email": answer_info['email']}, {"_id": False})
    questions = user['questions']
    questions.append({'question': answer_info['question'], 'answer': answer_info['answer']})
    users_collection.update_one({"email": answer_info['email']}, {"$set": {'questions': questions}})