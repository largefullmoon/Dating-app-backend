from pymongo import MongoClient
client = MongoClient("mongodb://127.0.0.1:27017/")
db = client["tyche_app"]
photos_collection = db["photos"]

def getPhotos(email):
    photos = photos_collection.find({'email': email})
    return photos
