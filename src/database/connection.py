import pymongo
import os
from pymongo import MongoClient
import dotenv
from dotenv import load_dotenv


MongoTOKEN = os.getenv("MongoTOKEN")
client = MongoClient(MongoTOKEN)
db = client.test
mod = db.moderation