from fastapi import FastAPI, File, UploadFile, Depends, Query, Form, Request, Header
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from datetime import datetime
from typing import List
import json
import utils
import asyncpg
import pandas as pd

DATABASE_URL = "postgresql://saim:R2_RkmUt3xc59Gjzuhn33A@joking-egret-7111.8nk.cockroachlabs.cloud:26257/defaultdb?sslmode=verify-full&sslrootcert=./cert/root.crt"

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

@app.post("/uploadfile/")
async def create_upload_file(files: List[UploadFile] = File(...)):
    recipes = []
    failed_files = []
    for file in files:
        try:
            data = utils.read_data(file.file,file.filename)
            recipes.append(data)
        except json.JSONDecodeError:
            failed_files.append(file.filename)
            # return JSONResponse(content={"error": "Invalid JSON data"}, status_code=400)
        except Exception as e:
            failed_files.append(file.filename)
            # return JSONResponse(content={"error": str(file.filename)}, status_code=500)
            # return {"error": [file.filename], "status_code":500}

    return {"recipes": recipes, "failed_files":failed_files}

@app.get("/damco-records/")
async def get_damco_data(status : str = Header(...),
        start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
        end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format")):
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        query = f"SELECT * FROM dmc_{status}_records"
        filters = []

        if start_date:
            filters.append(f"DATE(timestamp) >= '{start_date}'")
        if end_date:
            filters.append(f"DATE(timestamp) <= '{end_date}'")

        if filters:
            query += " WHERE " + " AND ".join(filters)

        rows = await conn.fetch(query)
        damco_records = [dict(row) for row in rows]
        damco_records.reverse()
    finally:
        await conn.close()

    return {"damco_records": damco_records}

@app.get("/damco-ammend-records/")
async def get_damco_ammend_data(status : str = Header(...),
        start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
        end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format")):
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        query = f"SELECT * FROM dmc_ammend_{status}_records"
        filters = []

        if start_date:
            filters.append(f"DATE(timestamp) >= '{start_date}'")
        if end_date:
            filters.append(f"DATE(timestamp) <= '{end_date}'")

        if filters:
            query += " WHERE " + " AND ".join(filters)

        rows = await conn.fetch(query)
        damco_ammend_records = [dict(row) for row in rows]
        damco_ammend_records.reverse()
    finally:
        await conn.close()

    return {"damco_ammend_records": damco_ammend_records}


@app.get("/nexus-records/")
async def get_nexus_data(status : str = Header(...),
        start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
        end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format")):
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        query = f"SELECT * FROM nxs_{status}_records"
        filters = []

        if start_date:
            filters.append(f"DATE(timestamp) >= '{start_date}'")
        if end_date:
            filters.append(f"DATE(timestamp) <= '{end_date}'")

        if filters:
            query += " WHERE " + " AND ".join(filters)

        rows = await conn.fetch(query)
        nexus_records =[dict(row) for row in rows]
        nexus_records.reverse()
    finally:
        await conn.close()

    return {"nexus_records": nexus_records}


@app.post("/upload-chemicals/")
def upload_chemicals(files: List[UploadFile] = File(...)):
    for file in files:
        try:
            file = pd.read_excel(file.file, na_values=[""], keep_default_na=False)
            headers = ['Washing Name', 'FULL_NAME', 'Cost_PerKG',
                           'KG_Per_Can', 'Cost_per_Unit_Of_usage', 'Cost_per_UOM',
                           'TYPE & USE', 'Unit Used', 'Unit Conversion']
            if list(file.columns) == headers:
                new_headers = {'Washing Name': 'name', 'FULL_NAME': 'full_name', 'Cost_PerKG': 'costPerKg',
                               'KG_Per_Can': 'kgPerCan', 'Cost_per_Unit_Of_usage': 'costPerUnit', 'Cost_per_UOM': 'costUom',
                               'TYPE & USE': 'typeAndUse', 'Unit Used': 'unitUsed', 'Unit Conversion': 'unitConversion'}

                for old_name, new_name in new_headers.items():
                    file.rename(columns={old_name: new_name}, inplace=True)

                for column in file.columns:
                    if file[column].dtype == 'object':  # Check for string (object) columns
                        file[column].fillna("", inplace=True)
                    elif pd.api.types.is_numeric_dtype(file[column]):  # Check for numeric columns
                        file[column].fillna(0, inplace=True)
                file_dict = file.to_dict(orient="records")
                return {"chemicals" : list(file_dict)}
            else:
                return JSONResponse(content={"error": "Invalid file format"}, status_code=500)
        except json.JSONDecodeError:
            return JSONResponse(content={"error": "Invalid JSON data"}, status_code=400)
        except Exception as e:
            return JSONResponse(content={"error": str(file.filename)}, status_code=500)
