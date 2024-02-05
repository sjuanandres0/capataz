from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

import os
mongoUri = os.getenv("mongoUri")
if mongoUri is None:
    from credentials import mongoUri

print(f'mongoUri:{mongoUri}')

client = MongoClient(mongoUri, server_api=ServerApi('1'))
collection = client.dummyDatabase.dummyCollection
result = list(collection.find_one())
result = collection.find_one()
print(result)
