from fastapi import FastAPI

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


patients_db = [
    {"patient_id": "P001", "name": "Chin", "test_result": "HBsAg negative"},
    {"patient_id": "P002", "name": "Loan", "test_result": "HBsAg positive"},
    {"patient_id": "P003", "name": "Diu", "test_result": "Anti-HBs positive"},
    {"patient_id": "P004", "name": "Hoang", "test_result": "HBsAg negative"},
    {"patient_id": "P005", "name": "Duc", "test_result": "Anti-HBs negative"}
]

@app.get("/patients/")
async def read_patients(skip: int = 0, limit: int = 10):
    return patients_db[skip : skip + limit]

@app.get("/patients/me")
async def read_current_patient():
    return {"patient_id": "current_patient", "message": "This is the current patient"}

@app.get("/patients/{patient_id}")
async def read_patient(patient_id: str, test_type: str | None = None, detailed: bool = False):
    patient = {"patient_id": patient_id}
    if test_type:
        patient["test_type"] = test_type
    if detailed:
        patient["details"] = "This patient has a detailed medical record"
    for p in patients_db:
        if p["patient_id"] == patient_id:
            patient.update(p)
            break
    return patient

@app.get("/patients/{patient_id}/test")
async def read_patient_test(patient_id: str, test_result: str):
    return {"patient_id": patient_id, "test_result": test_result}


