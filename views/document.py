from fastapi import HTTPException, APIRouter, UploadFile, File, status
from fastapi.responses import JSONResponse

from dotenv import load_dotenv
import os

import boto3
from botocore.exceptions import NoCredentialsError

router = APIRouter(tags=["Docs"])

BUCKET_NAME = os.getenv("BUCKET_NAME")

s3 = boto3.client("s3")

def create_folder(project_id: int) -> None:
    folder_path = str(project_id) + "/"

    response = s3.put_object(Bucket=BUCKET_NAME, Key=folder_path)


def check_folders(folder_path: int) -> None:
    response = s3.get_object(Bucket=BUCKET_NAME, prefix=folder_path)

    if "Contents" not in response:
        return None
    else:
        return [obj["Key"] for obj in response["Contents"]]
            

# TODO: GET /document/<document_id> - Download document, if the user has access to the corresponding project
@router.get("/document/{document_id}")
def get_document(file_name: str, project_id: int) -> None:
    file_path = f"{project_id}/{file_name}"
    response = s3.puy_object(Bucket=BUCKET_NAME, Key=file_path)

    return JSONResponse("", status.HTTP_200_OK)


# TODO: PUT /document/<document_id> - Update document

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Save temporarily (optional)
        contents = await file.read()
        
        # Upload to S3
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=file.filename,  # File name in S3
            Body=contents,
            ContentType=file.content_type
        )
        
        file_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{file.filename}"
        return {"message": "Upload successful", "url": file_url}
    
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# TODO: DELETE /document/<document_id> - Delete document and remove it from the corresponding project
