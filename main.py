from typing import Annotated
from fastapi import Body, FastAPI, Query, Path, HTTPException
from pydantic import BaseModel, Field, AfterValidator
import random

app = FastAPI()

fake_items_db = [{"item_name": "Chin"}, {"item_name": "Loan"},{"item_name": "Diu"} , {"item_name": "Hoang"}, {"item_name": "Duc"}]

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
    test_result: str | None = Field(
        None,
        min_length=3,
        title="Test Result",
        description="Result of the medical test"
    )
    test_date: str | None = Field(
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
    return patients_db[skip: skip + limit]

# Endpoint: Lấy thông tin bệnh nhân hiện tại
@app.get("/patients/me")
async def read_current_patient():
    patient = random.choice(patients_db)
    return {"patient_id": patient["patient_id"], "message": "This is the current patient", **patient}

# Endpoint: Lấy thông tin bệnh nhân theo patient_id
@app.get("/patients/{patient_id}")
async def read_patient(
    patient_id: Annotated[str, Path(validate=AfterValidator(check_valid_patient_id))],
    test_type: Annotated[
        str | None,
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
    patient = {"patient_id": patient_id}
    for p in patients_db:
        if p["patient_id"] == patient_id:
            patient.update(p)
            break
    else:
        raise HTTPException(status_code=404, detail="Patient not found")

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
    for p in patients_db:
        if p["patient_id"] == patient_id:
            return {"patient_id": patient_id, "test_result": test_result}
    raise HTTPException(status_code=404, detail="Patient not found")

# Endpoint: Tạo bệnh nhân mới
@app.post("/patients/")
async def create_patient(patient: Annotated[Patient, Body(embed=True)]):
    new_id = f"P{len(patients_db) + 1:03d}"
    patient_dict = patient.dict()
    patient_dict["patient_id"] = new_id
    patients_db.append(patient_dict)
    return patient_dict

# Endpoint: Cập nhật thông tin bệnh nhân
@app.put("/patients/{patient_id}")
async def update_patient(
    patient_id: Annotated[str, Path(validate=AfterValidator(check_valid_patient_id))],
    patient: Annotated[Patient, Body(embed=True)]
):
    patient_dict = patient.dict()
    patient_dict["patient_id"] = patient_id
    for i, existing_patient in enumerate(patients_db):
        if existing_patient["patient_id"] == patient_id:
            patients_db[i] = patient_dict
            return {"patient_id": patient_id, **patient_dict}
    raise HTTPException(status_code=404, detail="Patient not found")