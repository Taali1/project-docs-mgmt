from fastapi import HTTPException, APIRouter, UploadFile, File, status, Path, Depends, Response
from fastapi.responses import JSONResponse, StreamingResponse

from dotenv import load_dotenv
import os

from db.models import Permission 
from views.auth import auth_requierd
from db.db import check_permission, get_db

import aioboto3
from botocore.exceptions import NoCredentialsError, ClientError

router = APIRouter(tags=["Docs"])

load_dotenv()

BUCKET_NAME = os.getenv("BUCKET_NAME")

session = aioboto3.Session()

async def delete_s3_folder(project_id: int) -> None:
    prefix = f"{project_id}/"
    async with session.resource("s3") as s3:
        bucket = await s3.Bucket(BUCKET_NAME)
        await bucket.objects.filter(Prefix=prefix).delete()

async def get_s3_documents_list(project_id: int) -> list:
    prefix = f"{project_id}/"
    prefix_len = len(prefix)
    result = []

    async with session.resource("s3") as s3:
        bucket = await s3.Bucket(BUCKET_NAME)
        async for obj in bucket.objects.filter(Prefix=prefix):
            result.append(obj.key[prefix_len:])
    return result[1:]

async def upload_s3_file(file: UploadFile, project_id: int):
    async with aioboto3.client("s3") as s3:
        contents = await file.read()
        key = f"{project_id}/{file.filename}"
        await s3.put_object(
            Bucket=BUCKET_NAME,
            Key=key,
            Body=contents,
            ContentType=file.content_type
        )


@router.get("/document/{document_id:path}")
async def get_s3_document(download_web: str = False , document_id: str = Path(...), user_payload: dict = Depends(auth_requierd)) -> None:
    project_id = document_id.split("-")[0]
    with get_db() as conn:
        user_perm = await check_permission(conn, user_payload["sub"], project_id)

    if user_perm is not None:
        async with session.client("s3") as s3:
            # if you want to download file trough web explorer 
            if download_web:
                try:
                    response = await s3.get_object(Bucket=BUCKET_NAME,
                        Key=document_id,
                        Filename=document_id
                        )
                except s3.exceptions.NoSuchKey:
                    raise HTTPException(status_code=404, detail="File not found")

                stream = response["Body"]

                async def file_iterator(chunk_size=1024*1024):
                    async for chunk in stream.iter_chunks(chunk_size):
                        yield chunk
                
                return StreamingResponse(
                    file_iterator(),
                    media_type="application/octet-stream",
                    headers={"Content-Disposition": f"attachment; filename={document_id.split('-')[-1]}"}
            )
            # If you want to include file in json response
            else:
                try:
                    response = await s3.get_object(Bucket=BUCKET_NAME, Key=document_id)
                except s3.exceptions.NoSuchKey:
                    raise HTTPException(status_code=404, detail="File not found")

                content = await response["Body"].read()

                return Response(
                    content=content,
                    media_type="application/octet-stream",
                    headers={"Content-Disposition": f"attachment; filename={document_id.split('/')[-1]}"}
                )
    else:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized")


@router.post("/document/{document_id:path}")
async def upload_s3_file(file: UploadFile = File(...), document_id: str = Path(...), user_payload: dict = Depends(auth_requierd)):
    with get_db() as conn:
        user_perm = await check_permission(conn, user_payload["sub"], document_id)

    if user_perm is not None:
        try:
            async with session.resource("s3") as s3:
                contents = await file.read()
                
                await s3.put_object(
                    Bucket=BUCKET_NAME,
                    Key=document_id,
                    Body=contents,
                    ContentType=file.content_type
                )
                
                return JSONResponse(f"File saved with name: {document_id}", status.HTTP_200_OK)
    
        except NoCredentialsError:
            raise HTTPException(status_code=500, detail="AWS credentials not found")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@router.delete("/document/{document_id:path}")
async def delete_s3_document(document_id: str) -> JSONResponse:
    try:
        async with session.client("s3") as s3:
            await s3.delete_object(
                Bucket=BUCKET_NAME,
                Key=document_id
            )

    except ClientError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))