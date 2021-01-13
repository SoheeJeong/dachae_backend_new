import os
import boto3
from boto3.s3.transfer import S3Transfer
from botocore.client import Config
from datetime import date,datetime

from .models import TbUserAuth,TbUserInfo
import dachae.exceptions as exceptions

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
                ExpiresIn=expiration, #expiration sec 이후에 만료
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

def age_range_calulator(birthday_date):
    todays_date = date.today()
    
    birthday_split_list = birthday_date.split("-")
    born_year = int(birthday_split_list[0])
    born_month = int(birthday_split_list[1])
    born_day = int(birthday_split_list[2])

    age = todays_date.year - born_year - ((todays_date.month, todays_date.day) < (born_month, born_day))
    if age < 10:
        age_range = "10세 이하"
    elif age < 20:
        age_range = "10-19"
    elif age < 30:
        age_range = "20-29"
    elif age < 40:
        age_range = "30-39"
    elif age < 50:
        age_range = "40-49"
    elif age < 60:
        age_range = "50-59"
    elif age < 70:
        age_range = "60-69"
    elif age < 80:
        age_range = "70-79"
    elif age < 90:
        age_range = "80-89"
    elif age < 100:
        age_range = "90-99"
    else:
        age_range = "100세 이상"

    return age_range



def check_token_isvalid(access_token,user_id):
    if user_id==None and access_token==None:
        return "not logged"

    user = TbUserInfo.objects.filter(user_id=user_id)
    
    if user.exists():
        #토큰이 존재하지 않음
        if access_token == None:
            raise exceptions.ParameterMissingException

        user_info = user.values("social_id","social_platform","state")[0]
        social_id = user_info["social_id"]
        social_platform = user_info["social_platform"]

        userauth_info = TbUserAuth.objects.filter(social_id=social_id,social_platform=social_platform).values("access_token","expire_time")[0]
        
        #인증토큰 불일치
        if access_token != userauth_info["access_token"]:
            raise exceptions.InvalidAccessTokenException
        #expire time이 지남
        elif userauth_info["expire_time"] <= datetime.now():
            raise exceptions.ExpiredAccessTokenException

        #TODO: check user status (휴면,탈퇴여부) -> 적절한 exception 
        if user_info["state"] == "withdrawn":
            raise exceptions.LeftMemberException
        elif user_info["state"] == "dormant":
            raise exceptions.DormantMemberException
        
    else:
        # return "no user exists"
        raise exceptions.InvalidUserIdException

    return "valid user"

def get_expire_time_from_expires_in(expires_in):
    ts = datetime.now() + datetime.timedelta(seconds=expires_in)
    expire_time = ts.strftime('%Y-%m-%d %H:%M:%S')
    return expire_time