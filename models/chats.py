from pymongo import MongoClient

client = MongoClient("mongodb://127.0.0.1:27017/")
db = client["Tyche"]
chats_collection = db["chats"]

def getLastMessage(main_email, chatUser_email):
    print(main_email)
    print(chatUser_email)
    chats = chats_collection.find({
        "$or": [
            {'from': main_email, 'to': chatUser_email},
            {'from': chatUser_email, 'to': main_email}
        ]
    }, {'_id': False})
    chats = list(chats)
    if chats:  # Check if the list is not empty
        chat = chats[-1]  # Get the last item in the list
    else:
        chat = None  # Handle case when the list is empty
    if chat:
        if 'message' in chat:
            return chat['message']
        else:
            return 'no chats'
    else:
        return 'no chats'

def insertChat(chat_info):
    print(chat_info)
    if 'from' in chat_info and 'to' in chat_info and 'message' in chat_info:
        chats_collection.insert_one({
            'from': chat_info['from'],
            'to': chat_info['to'],
            'message': chat_info['message'],
            'time': chat_info['time']
        })
        return True
    else:
        return False

async def getChats(params):
    chats = chats_collection.find({
        '$or': [
            {'from': params['from'], 'to': params['to']},
            {'from': params['to'], 'to': params['from']}
        ]
    }, {'_id': False})
    
    if chats:
        return list(chats)  # Convert the cursor to a list
    else:
        return []
