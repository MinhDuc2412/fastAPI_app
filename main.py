from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from typing import Annotated, Optional
from fastapi import Query, Path, Body
from pydantic.functional_validators import AfterValidator
import jwt
import random
import os
from pymongo import MongoClient
from bson.objectid import ObjectId  
import logging
from fastapi import FastAPI, HTTPException, Request
from starlette.responses import JSONResponse
from datetime import datetime


app = FastAPI()

# Kết nối MongoDB
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/mydatabase')
client = MongoClient(MONGO_URI)
db = client["mydatabase"]
patients_collection = db["patients"]


# fake_items_db = [{"item_name": "Chin"}, {"item_name": "Loan"},{"item_name": "Diu"} , {"item_name": "Hoang"}, {"item_name": "Duc"}]

# @app.get("/items/{item_id}")
# async def read_item(item_id):
#     return {"item_id": item_id}

# @app.get("/users/Duc")
# async def read_user_me():
#     return {"user_id": "the current user"}


# @app.get("/users/{user_id}")
# async def read_user(user_id: str):
#     return {"user_id": user_id}

# @app.get("/users")
# async def read_users():
#     return ["Duc1", "Duc2"]


# @app.get("/users")
# async def read_users2():
#     return ["Duc3", "Duc4"]

# @app.get("/items/")
# async def read_item(skip: int = 0, limit: int = 10):
#     return fake_items_db[skip : skip + limit]

# @app.get("/items/{item_id}")
# async def read_item(item_id: str, q: str | None = None):
#     if q:
#         return {"item_id": item_id, "q": q}
#     return {"item_id": item_id}

# @app.get("/items/{item_id}")
# async def read_item(item_id: str, q: str | None = None, short: bool = False):
#     item = {"item_id": item_id}
#     if q:
#         item.update({"q": q})
#     if not short:
#         item.update(
#             {"description": "This is an amazing item that has a long description"}
#         )
#     return item

# @app.get("/items/{item_id}")
# async def read_user_item(item_id: str, needy: str):
#     item = {"item_id": item_id, "needy": needy}
#     return item

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = "my-secret-key"
ALGORITHM = "HS256"

# Danh sách bệnh nhân mẫu
patients_db = [
    {"patient_id": "P001", "name": "Chin", "test_result": "HBsAg negative", "test_date": "2025-08-01"},
    {"patient_id": "P002", "name": "Loan", "test_result": "HBsAg positive", "test_date": "2025-08-02"},
    {"patient_id": "P003", "name": "Diu", "test_result": "Anti-HBs positive", "test_date": "2025-08-03"},
    {"patient_id": "P004", "name": "Hoang", "test_result": "HBsAg negative", "test_date": "2025-08-04"},
    {"patient_id": "P005", "name": "Duc", "test_result": "Anti-HBs negative", "test_date": "2025-08-05"}
]

# Mô hình Pydantic cho bệnh nhân
class Patient(BaseModel):
    name: str = Field(..., min_length=1, title="Patient Name", description="Full name of the patient")
    test_result: Optional[str] = Field(
        None,
        min_length=3,
        title="Test Result",
        description="Result of the medical test"
    )
    test_date: Optional[str] = Field(
        None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",  
        title="Test Date",
        description="Date of the test in YYYY-MM-DD format"
    )

# Hàm xác thực patient_id
def check_valid_patient_id(patient_id: str) -> str:
    if not (patient_id.startswith("P") and len(patient_id) == 4 and patient_id[1:].isdigit()):
        raise ValueError('Invalid patient_id format, it must be "P" followed by 3 digits')
    return patient_id

# Endpoint: Lấy danh sách bệnh nhân với phân trang
@app.get("/patients/")
async def read_patients(
    skip: Annotated[
        int,
        Query(
            title="Skip",
            description="Number of patients to skip for pagination",
            ge=0
        )
    ] = 0,
    limit: Annotated[
        int,
        Query(
            title="Limit",
            description="Maximum number of patients to return",
            ge=1,
            le=100
        )
    ] = 10
):
    try:
        logger.info(f"Fetching patients with skip={skip}, limit={limit}")
        patients = list(patients_collection.find().skip(skip).limit(limit))
        logger.info(f"Found {len(patients)} patients")
        for patient in patients:
            patient["_id"] = str(patient["_id"])
        return patients
    except Exception as e:
        logger.error(f"Error in read_patients: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Endpoint: Lấy thông tin bệnh nhân hiện tại (ngẫu nhiên)
@app.get("/patients/me")
async def read_current_patient():
    try:
        patient = patients_collection.aggregate([{"$sample": {"size": 1}}]).next()
        if patient:
            patient["_id"] = str(patient["_id"])
            return {"patient_id": patient.get("patient_id"), "message": "This is the current patient", **patient}
        raise HTTPException(status_code=404, detail="No patients found")
    except StopIteration:
        raise HTTPException(status_code=404, detail="No patients found")

# Endpoint: Lấy thông tin bệnh nhân theo patient_id
@app.get("/patients/{patient_id}")
async def read_patient(
    patient_id: Annotated[str, Path(validate=AfterValidator(check_valid_patient_id))],
    test_type: Annotated[
        Optional[str],
        Query(
            title="Test Type",
            description="Filter by specific test type",
            min_length=3,
            deprecated=True
        )
    ] = None,
    detailed: Annotated[
        bool,
        Query(
            title="Detailed Info",
            description="Include detailed medical record if true"
        )
    ] = False
):
    patient = patients_collection.find_one({"patient_id": patient_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    patient["_id"] = str(patient["_id"])
    if test_type:
        patient["test_type"] = test_type
    if detailed:
        patient["details"] = "This patient has a detailed medical record"
    return patient

# Endpoint: Lấy kết quả xét nghiệm của bệnh nhân
@app.get("/patients/{patient_id}/test")
async def read_patient_test(
    patient_id: Annotated[str, Path(validate=AfterValidator(check_valid_patient_id))],
    test_result: Annotated[
        str,
        Query(
            title="Test Result",
            description="Specific test result to filter",
            min_length=3
        )
    ]
):
    patient = patients_collection.find_one({"patient_id": patient_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"patient_id": patient_id, "test_result": patient.get("test_result", test_result)}

# Endpoint: Tạo bệnh nhân mới
@app.post("/patients/")
async def create_patient(
    patient: Annotated[Patient, Body(embed=True)]
):
    existing_ids = [p["patient_id"] for p in patients_collection.find({}, {"patient_id": 1})]
    new_id = f"P{len(existing_ids) + 1:03d}"
    patient_dict = patient.dict()
    patient_dict["patient_id"] = new_id
    patient_dict["created_at"] = datetime.now().isoformat()
    result = patients_collection.insert_one(patient_dict)
    patient_dict["_id"] = str(result.inserted_id)
    return patient_dict

# Endpoint: Cập nhật thông tin bệnh nhân
@app.put("/patients/{patient_id}")
async def update_patient(
    patient_id: Annotated[str, Path(validate=AfterValidator(check_valid_patient_id))],
    patient: Annotated[Patient, Body(embed=True)]
):
    patient_dict = patient.dict()
    patient_dict["patient_id"] = patient_id
    patient_dict["updated_at"] = datetime.now().isoformat()
    result = patients_collection.replace_one({"patient_id": patient_id}, patient_dict, upsert=True)
    if result.matched_count == 0 and result.upserted_id is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"patient_id": patient_id, **patient_dict}