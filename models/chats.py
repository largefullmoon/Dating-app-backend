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
	if chat:
		if 'message' in chat:
			return chat['message']
		else:
			return 'Hello, how are you?'
	else:
		return 'Hello, how are you?'
def insertChat(chat_info):
	print(chat_info)
	chats_collection.insert_one({'from': chat_info['from'], 'to': chat_info['to'], 'message': chat_info['message'], 'time': chat_info['time']})
	return True
	pass
