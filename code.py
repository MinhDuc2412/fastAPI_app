from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

MONGO_URI = "mongodb://localhost:27017/"  # Dùng port mặc định

def test_mongo_connection():
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("MongoDB connection successful!")
        print("Databases:", client.list_database_names())
    except ConnectionFailure as e:
        print(f"MongoDB connection failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    test_mongo_connection()