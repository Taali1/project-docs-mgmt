from fastapi import HTTPException, APIRouter, UploadFile, File, status, Path, Depends, Response
from fastapi.responses import JSONResponse, StreamingResponse

from dotenv import load_dotenv
import os

from views.auth import auth_requierd
from db.db import check_permission, get_db

import aioboto3
from botocore.exceptions import NoCredentialsError, ClientError

router = APIRouter(tags=["Docs"])

load_dotenv()

BUCKET_NAME = os.getenv("BUCKET_NAME")
ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS").split(",")

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

async def check_file_extension(files: list[UploadFile]) -> bool:
    if not isinstance(files, list):
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Wrong data type"
        )

    for file in files:
        # Safely get extension with dot
        parts = file.filename.lower().rsplit(".", 1)
        if len(parts) != 2:
            raise HTTPException(
                status.HTTP_406_NOT_ACCEPTABLE,
                detail=f"File '{file.filename}' has no extension"
            )
        ext = "." + parts[1]

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status.HTTP_406_NOT_ACCEPTABLE,
                detail=f"Only {', '.join(ALLOWED_EXTENSIONS)} files are allowed"
            )

    return True


@router.get("/projects/{project_id}/documents/{document_id}")
async def get_s3_document(project_id: str, download_web: str = False , document_id: str = Path(...), user_payload: dict = Depends(auth_requierd)) -> None:
    key = f"{project_id}/{document_id}"
    with get_db() as conn:
        user_perm = await check_permission(conn, user_payload["sub"], int(project_id))

    if user_perm is not None:
        async with session.client("s3") as s3:
            # if you want to download file trough web explorer 
            if download_web:
                try:
                    response = await s3.get_object(
                        Bucket=BUCKET_NAME,
                        Key=key,
                        Filename=key
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
                    response = await s3.get_object(
                        Bucket=BUCKET_NAME, 
                        Key=key, 
                        Filename=key)
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


@router.post("/projects/{project_id}/documents/{document_id}")
async def upload_s3_file(file: UploadFile = File(...),project_id: str = Path(...), document_id: str = Path(...), user_payload: dict = Depends(auth_requierd)):
    key = f"{project_id}/{document_id}"

    check_file_extension([file])

    with get_db() as conn:
        user_perm = await check_permission(conn, user_payload["sub"], document_id)

    if user_perm is not None:
        try:
            async with session.resource("s3") as s3:
                contents = await file.read()
                
                await s3.put_object(
                    Bucket=BUCKET_NAME,
                    Key=key,
                    Body=contents,
                    ContentType=file.content_type
                )
                
                return JSONResponse(f"File saved with name: {document_id}", status.HTTP_200_OK)
    
        except NoCredentialsError:
            raise HTTPException(status_code=500, detail="AWS credentials not found")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@router.delete("/projects/{project_id}/documents/{document_id}")
async def delete_s3_document(project_id: str = Path(...), document_id: str = Path(...)) -> JSONResponse:
    key = f"{project_id}/{document_id}"
    try:
        async with session.client("s3") as s3:
            await s3.delete_object(
                Bucket=BUCKET_NAME,
                Key=key
            )

    except ClientError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))