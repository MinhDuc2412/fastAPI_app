from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from typing import Annotated, Optional
from fastapi import Query, Path, Body
from pydantic.functional_validators import AfterValidator
import jwt  
import random

app = FastAPI()

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

# Hàm kiểm tra username/password
def verify_user(username: str, password: str) -> dict:
    if username == "admin" and password == "password":  # Thay bằng kiểm tra DB
        return {"sub": username, "role": "admin"}
    elif username == "doctor" and password == "password":
        return {"sub": username, "role": "doctor"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

# Hàm kiểm tra token
def is_valid_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Middleware: Kiểm tra HTTPS và token cơ bản
@app.middleware("http")
async def check_token_and_https(request: Request, call_next):
    if request.url.path.startswith("/patients"):
        # Bỏ kiểm tra HTTPS khi chạy local
        # if request.url.scheme != "https":
        #     raise HTTPException(status_code=403, detail="HTTPS required")
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token or not is_valid_token(token):
            raise HTTPException(status_code=401, detail="Invalid or missing token")
    response = await call_next(request)
    return response

# Endpoint đăng nhập để sinh token
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = verify_user(form_data.username, form_data.password)
    token = jwt.encode(user, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}

# Security: Kiểm tra quyền admin
async def require_admin(token: str = Depends(oauth2_scheme)):
    payload = is_valid_token(token)
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return payload

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

# Endpoint: Tạo bệnh nhân mới (chỉ admin)
@app.post("/patients/")
async def create_patient(
    patient: Annotated[Patient, Body(embed=True)],
    token: dict = Depends(require_admin)
):
    new_id = f"P{len(patients_db) + 1:03d}"
    patient_dict = patient.dict()
    patient_dict["patient_id"] = new_id
    patients_db.append(patient_dict)
    return patient_dict

# Endpoint: Cập nhật thông tin bệnh nhân (chỉ admin)
@app.put("/patients/{patient_id}")
async def update_patient(
    patient_id: Annotated[str, Path(validate=AfterValidator(check_valid_patient_id))],
    patient: Annotated[Patient, Body(embed=True)],
    token: dict = Depends(require_admin)
):
    patient_dict = patient.dict()
    patient_dict["patient_id"] = patient_id
    for i, existing_patient in enumerate(patients_db):
        if existing_patient["patient_id"] == patient_id:
            patients_db[i] = patient_dict
            return {"patient_id": patient_id, **patient_dict}
    raise HTTPException(status_code=404, detail="Patient not found")