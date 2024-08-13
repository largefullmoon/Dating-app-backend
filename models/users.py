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
    users = users_collection.find({'isVerified': True, 'termsAgreed': True})
    return users
def getUser(where):
    user = users_collection.find_one({'isVerified': True, 'termsAgreed': True})
    return user