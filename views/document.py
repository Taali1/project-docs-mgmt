from fastapi import HTTPException, APIRouter, UploadFile, File, status, Path
from fastapi.responses import JSONResponse

from dotenv import load_dotenv
import os

import boto3
from botocore.exceptions import NoCredentialsError, ClientError

router = APIRouter(tags=["Docs"])

load_dotenv()

BUCKET_NAME = os.getenv("BUCKET_NAME")
AWS_ACCESS_KEY_ID = os.getenv()
AWS_SECRET_ACCESS_KEY = os.getenv()
AWS_REGION_NAME = os.getenv()

s3 = boto3.client("s3")

def aws_create_folder(project_id: int) -> None:
    folder_path = str(project_id) + "/"

    response = s3.put_object(
        Bucket=BUCKET_NAME, 
        Key=folder_path
        )


def aws_check_folders(folder_path: int) -> None:
    response = s3.get_object(Bucket=BUCKET_NAME, prefix=folder_path)

    if "Contents" not in response:
        return None
    else:
        return [obj["Key"] for obj in response["Contents"]]
            

# TODO: GET /document/<document_id> - Download document, if the user has access to the corresponding project
@router.get("/document/{document_id}")
def aws_get_document(file_name: str, project_id: int) -> None:
    file_path = f"{project_id}/{file_name}"
    response = s3.puy_object(Bucket=BUCKET_NAME, Key=file_path)

    return JSONResponse("", status.HTTP_200_OK)


# TODO: PUT /document/<document_id> - Update document

@router.post("/document/{document_id}")
async def aws_upload_file(file: UploadFile = File(...), document_id: str = Path(...)):
    try:
        contents = await file.read()
        
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=file.filename,
            Body=contents,
            ContentType=file.content_type
        )
        
        file_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{file.filename}"
        return {"message": "Upload successful", "url": file_url}
    
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/document/{document_id}")
async def delete_file(document_id: str) -> JSONResponse:
    try:
        s3.delete_object(
            Bucket=BUCKET_NAME,
            Key=document_id
        )

    except ClientError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))