from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import json
import utils 

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
    for file in files:
        try:
            data = utils.read_data(file.file,file.filename)
            recipes.append(data)
        except json.JSONDecodeError:
            return JSONResponse(content={"error": "Invalid JSON data"}, status_code=400)
        except Exception as e:
            return JSONResponse(content={"error": str(e)}, status_code=500)

    return {"recipes": recipes}
