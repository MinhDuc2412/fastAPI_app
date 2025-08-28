from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from pydantic import BaseModel
from typing import List

# MongoDB connection URI
MONGO_URI = "mongodb://admin:241203@localhost:27018/admin"

# Create FastAPI app
app = FastAPI()

# Connect to MongoDB client
client = MongoClient(MONGO_URI)

# Select the MongoDB database and collection
db = client.test_db
collection = db.test_collection

# Verify connection
try:
    client.admin.command('ping')
    print("MongoDB connection successful!")
except ConnectionFailure as e:
    print(f"MongoDB connection failed: {e}")


# Pydantic model for input validation
class Item(BaseModel):
    name: str
    description: str

# Endpoint to create a new item in MongoDB
@app.post("/items/")
async def create_item(item: Item):
    try:
        # Insert the item into MongoDB collection
        result = collection.insert_one(item.dict())
        return {"id": str(result.inserted_id), "name": item.name, "description": item.description}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inserting item: {e}")

# Endpoint to get all items from MongoDB
@app.get("/items/", response_model=List[Item])
async def get_items():
    try:
        items = collection.find()
        return [{"name": item["name"], "description": item["description"]} for item in items]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving items: {e}")

# Endpoint to get an item by ID
@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: str):
    try:
        item = collection.find_one({"_id": item_id})
        if item:
            return {"name": item["name"], "description": item["description"]}
        else:
            raise HTTPException(status_code=404, detail="Item not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving item: {e}")
