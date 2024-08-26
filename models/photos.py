from pymongo import MongoClient
client = MongoClient("mongodb://127.0.0.1:27017/")
db = client["Tyche"]
photos_collection = db["photos"]

def getAllUsers(email):
    photos = photos_collection.find({'isVerified': True, 'termsAgreed': True})
    return photos
