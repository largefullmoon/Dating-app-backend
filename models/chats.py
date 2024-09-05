from pymongo import MongoClient
client = MongoClient("mongodb://127.0.0.1:27017/")
db = client["Tyche"]
chats_collection = db["chats"]

def getLastMessage(main_email, chatUser_email):
	chat = chats_collection.find_one({
     	"$or":
     	[
		    {'from':main_email, 'to':chatUser_email, 'last': True},
		    {'from':chatUser_email, 'to':main_email, 'last': True}
	  	]
	}, {'_id': False})
	if 'message' in chat:
		return chat['message']
	else:
		return ''
