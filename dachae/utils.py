import os
import boto3
from boto3.s3.transfer import S3Transfer
from botocore.client import Config

#TODO: expiration time 줄이기

class S3Connection():
    def __init__(self):
        AWS_S3_CREDS = {
            "aws_access_key_id": os.getenv("AWS_ACCESS_KEY"),
            "aws_secret_access_key":os.getenv("AWS_SECRET_KEY"),
            "config" : Config(signature_version='s3v4'),
            "region_name" : 'ap-northeast-2'
        }
        # S3 client
        self.s3_client = boto3.client('s3',**AWS_S3_CREDS)

    def get_presigned_url(self,bucket,key,expiration=3600):
        """Generate a presigned URL to share an S3 object

        :param bucket_name: string
        :param object_name: string
        :param expiration: Time in seconds for the presigned URL to remain valid
        :return: Presigned URL as string. If error, returns None.
        """
        # Generate the URL to get 'key-name' from 'bucket-name'
        try:
            url = self.s3_client.generate_presigned_url(
                ClientMethod='get_object',
                Params={
                    'Bucket': bucket,
                    'Key': key
                },
                ExpiresIn=expiration #expiration sec 이후에 만료
            )
        except:
            return None

        return url

    def upload_file_into_s3(self,filepath,bucket,key):
        try:
            transfer = S3Transfer(self.s3_client)
            transfer.upload_file(filepath,bucket,key)
        except:
            return None
        return key

     # def download_file_from_s3(savepath,bucket,key):
        #     try:
        #         s3_client.download_file(bucket,key,savepath)
        #     except:
        #         return None
        #     return savepath