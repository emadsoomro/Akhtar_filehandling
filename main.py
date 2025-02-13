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

DATABASE_URL = "postgres://akhtar11:9T0NMeQlomBAVtZ4_Q9RlA@grim-oribi-16146.8nj.gcp-europe-west1.cockroachlabs.cloud:26257/dev_db?sslmode=require"

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
            df_file = pd.read_excel(file.file, na_values=[""], keep_default_na=False)
            headers_1 = ['Washing Name', 'FULL_NAME', 'Cost_PerKG',
                           'KG_Per_Can', 'Cost_per_Unit_Of_usage', 'Cost_per_UOM',
                           'TYPE & USE', 'Unit Used', 'Unit Conversion']

            if list(df_file.columns) == headers_1:
                new_headers = {'Washing Name': 'name', 'FULL_NAME': 'full_name', 'Cost_PerKG': 'cost_per_kg',
                               'KG_Per_Can': 'kg_per_can', 'Cost_per_Unit_Of_usage': 'cost_per_unit', 'Cost_per_UOM': 'cost_uom',
                               'TYPE & USE': 'type_and_use', 'Unit Used': 'unit_used', 'Unit Conversion': 'unit_conversion'}

                for old_name, new_name in new_headers.items():
                    df_file.rename(columns={old_name: new_name}, inplace=True)

                for column in df_file.columns:
                    if df_file[column].dtype == 'object':  # Check for string (object) columns
                        df_file[column].fillna("", inplace=True)
                    elif pd.api.types.is_numeric_dtype(df_file[column]):  # Check for numeric columns
                        df_file[column].fillna(0, inplace=True)
                file_dict = df_file.to_dict(orient="records")
                return {"chemicals" : list(file_dict)}

            else:
                df_file = pd.read_excel(file.file, sheet_name="Order", na_values=[""], keep_default_na=False)
                headers_2 = ['Stock Sheet Chemical', 'Recipe Chemical', 'TYPE & USE', 'Cost_PerKG', 'KG_Per_Can', 'Free',
                             'On Order', 'Total', 'Requirement', 'Order', 'Boxes', 'Cost']
                df_file.columns = df_file.iloc[0]
                file_headers = list(df_file.columns)[:12]
                if file_headers == headers_2:
                    new_headers = {'Recipe Chemical': 'name', 'Stock Sheet Chemical': 'full_name',
                                   'Cost_PerKG': 'cost_per_kg', 'KG_Per_Can': 'kg_per_can', 'Free': 'free',
                                   'Cost': 'cost', 'TYPE & USE': 'type_and_use', 'On Order': 'on_order',
                                   'Total': 'total', 'Requirement': 'requirement', 'Order': 'order', 'Boxes': 'boxes'}

                    df_file = df_file.iloc[1:, :12]
                    for old_name, new_name in new_headers.items():
                        df_file.rename(columns={old_name: new_name}, inplace=True)

                    df_file['full_name'].fillna("", inplace=True)
                    df_file['name'].fillna("", inplace=True)
                    df_file['type_and_use'].fillna("", inplace=True)
                    for column in df_file.columns:
                        df_file[column].fillna(0, inplace=True)
                    df_cleaned = df_file[df_file['name'].notna() & (df_file['name'] != "")]
                    file_dict = df_cleaned.to_dict(orient="records")
                    return {"chemicals" : list(file_dict)}

                else:
                    return JSONResponse(content={"error": "Invalid file format"}, status_code=500)

        except json.JSONDecodeError:
            return JSONResponse(content={"error": "Invalid JSON data"}, status_code=400)
        except Exception as e:
            return JSONResponse(content={"error": str(file.filename)}, status_code=500)
