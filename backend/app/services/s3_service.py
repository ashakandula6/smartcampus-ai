import boto3
import io
from botocore.exceptions import ClientError
from app.core.config import get_settings

settings = get_settings()


class S3Service:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        self.bucket = settings.S3_BUCKET_NAME

    def upload_pdf(self, file_bytes: bytes, s3_key: str) -> str:
        """Upload PDF bytes to S3, return the s3_key."""
        self.client.put_object(
            Bucket=self.bucket,
            Key=s3_key,
            Body=file_bytes,
            ContentType="application/pdf",
        )
        return s3_key

    def upload_bytes(self, data: bytes, s3_key: str, content_type: str = "application/octet-stream") -> str:
        """Upload raw bytes (used for FAISS index)."""
        self.client.put_object(
            Bucket=self.bucket,
            Key=s3_key,
            Body=data,
            ContentType=content_type,
        )
        return s3_key

    def download_bytes(self, s3_key: str) -> bytes:
        """Download file from S3 as bytes."""
        response = self.client.get_object(Bucket=self.bucket, Key=s3_key)
        return response["Body"].read()

    def get_presigned_url(self, s3_key: str, expiry: int = 3600) -> str:
        """Generate a pre-signed URL for temporary download access."""
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": s3_key},
            ExpiresIn=expiry,
        )

    def delete_object(self, s3_key: str):
        """Delete a file from S3."""
        self.client.delete_object(Bucket=self.bucket, Key=s3_key)

    def ensure_bucket_exists(self):
        """Create bucket if it doesn't exist (run at startup)."""
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                if settings.AWS_REGION == "us-east-1":
                    self.client.create_bucket(Bucket=self.bucket)
                else:
                    self.client.create_bucket(
                        Bucket=self.bucket,
                        CreateBucketConfiguration={"LocationConstraint": settings.AWS_REGION},
                    )
                # Block public access
                self.client.put_public_access_block(
                    Bucket=self.bucket,
                    PublicAccessBlockConfiguration={
                        "BlockPublicAcls": True,
                        "IgnorePublicAcls": True,
                        "BlockPublicPolicy": True,
                        "RestrictPublicBuckets": True,
                    },
                )


s3_service = S3Service()
