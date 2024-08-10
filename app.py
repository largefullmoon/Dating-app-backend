from flask import Flask
from pymongo import MongoClient
from flask import Flask, request, jsonify, send_file, Response, stream_with_context
from flask_cors import CORS
import hashlib
from twilio.rest import Client
import random


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Adjust the origin to your React app's URL
cors = CORS(app, resources={r"/*": {"origins": "*"}}, methods=["GET", "POST", "OPTIONS"])
app.app_context().push()

client = MongoClient("mongodb://127.0.0.1:27017/")
db = client["Tyche"]
users_collection = db["users"]
chats_collection = db["chats"]