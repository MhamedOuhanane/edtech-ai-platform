"""Accès MinIO/S3 pour les fichiers de documents."""

import os

import boto3


# Client S3 compatible MinIO construit à partir des variables d'environnement.
def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=os.getenv("MINIO_ENDPOINT"),
        aws_access_key_id=os.getenv("MINIO_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("MINIO_SECRET_KEY"),
        region_name=os.getenv("MINIO_REGION", "us-east-1"),
        use_ssl=os.getenv("MINIO_SECURE", "False").lower() == "true",
    )


def get_bucket_name() -> str:
    return os.getenv("MINIO_BUCKET_NAME", "documents")


def upload_file(file_obj, key: str) -> None:
    client = get_s3_client()
    client.upload_fileobj(file_obj, get_bucket_name(), key)


def get_presigned_url(key: str, expires_in: int = 3600) -> str:
    client = get_s3_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": get_bucket_name(), "Key": key},
        ExpiresIn=expires_in,
    )


def delete_file(key: str) -> None:
    client = get_s3_client()
    client.delete_object(Bucket=get_bucket_name(), Key=key)