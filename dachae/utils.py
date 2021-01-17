import os
import boto3
from boto3.s3.transfer import S3Transfer
from botocore.client import Config
from botocore.errorfactory import ClientError
import datetime

from .models import TbUserAuth,TbUserInfo,TbArtworkInfo
import dachae.exceptions as exceptions

#TODO: expiration time 줄이기?

class S3Connection():
    def __init__(self):
        AWS_S3_CREDS = {
            "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_REMOTE"), 
            "aws_secret_access_key":os.getenv("AWS_SECRET_KEY_REMOTE"),
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
        # check if object exists
        try:
            self.s3_client.head_object(Bucket=bucket, Key=key)
        except ClientError:
            return "file does not exists in s3 bucket"

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
            return "AWS S3 connection failed"

        return url

    def convert_recommended_img_path_into_s3_path(self,recommend_results):
        analog,comp,mono = recommend_results
        ARTWORK_BUCKET_NAME = os.getenv("ARTWORK_BUCKET_NAME")

        for i in range(len(analog)):
            img_key = analog[i]["img_path"].values[0]
            del analog[i]["img_path"]
            analog[i].update({
                "img_path": self.get_presigned_url(ARTWORK_BUCKET_NAME,img_key)
            })
        for i in range(len(comp)):
            img_key = comp[i]["img_path"].values[0]
            del comp[i]["img_path"]
            comp[i].update({
                "img_path": self.get_presigned_url(ARTWORK_BUCKET_NAME,img_key)
                })
        for i in range(len(mono)):
            img_key = mono[i]["img_path"].values[0]
            del mono[i]["img_path"]
            mono[i].update({
                "img_path": self.get_presigned_url(ARTWORK_BUCKET_NAME,img_key)
                })
        return analog,comp,mono

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
    todays_date = datetime.date.today()
    
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



def check_token_isvalid(access_token,user_id,restrict=True):
    '''
    로그인이 필요없는 기능인 경우 restrict=False 로 설정
    '''
    if user_id==None and access_token==None:
        return "not logged"
    
    if (user_id and access_token) == None:
        print(user_id,access_token)
        raise exceptions.ParameterMissingException

    user = TbUserInfo.objects.filter(user_id=user_id)
    
    if user.exists():
        #토큰이 존재하지 않음
        if access_token == None:
            if not restrict:
                return "no token"
            raise exceptions.ParameterMissingException

        user_info = user.values("state")[0]

        userauth_info = TbUserAuth.objects.filter(user_id=user_id).values("access_token","expire_time")[0]
        
        #인증토큰 불일치
        if access_token != userauth_info["access_token"]:
            if not restrict:
                return "invalid token"
            raise exceptions.InvalidAccessTokenException
        #expire time이 지남
        elif userauth_info["expire_time"] <= datetime.datetime.now():
            if not restrict:
                return "expired token"
            raise exceptions.ExpiredAccessTokenException

        # check user status (휴면,탈퇴여부)
        if user_info["state"] == "withdrawn":
            if not restrict:
                return "withdrawn"
            raise exceptions.LeftMemberException
        elif user_info["state"] == "dormant":
            if not restrict:
                return "dormant"
            raise exceptions.DormantMemberException        
    else:
        if not restrict:
            return "no user exists"
        raise exceptions.InvalidUserIdException

    return "valid user"

def get_expire_time_from_expires_in(expires_in):
    ts = datetime.datetime.now() + datetime.timedelta(seconds=expires_in)
    expire_time = ts.strftime('%Y-%m-%d %H:%M:%S')
    return expire_time

def get_random_string(length):
    import random
    import string
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

def get_label_filtered_result(label_list,matching_result=None):
    """
    선택된 라벨인 label_list 가 포함된 이미지의 합집합을 반환한다.
    이미지에 선택된 라벨이 몇개가 포함되었는지(count)와 어떤 라벨인지(label list)도 도출한다.
    execRecommend 와 getPictureFilteredResult 에서 사용된다.
    """
    #execrecommend
    if matching_result:
        analog,comp,mono = matching_result
        return analog,comp,mono
    else:
        label_query = None
        #입력으로 받은 라벨 하나에 대해 해당 라벨을 포함하고 있는 artwork object들의 합집합
        for label_dict in label_list: 
            #TODO: artwork 별로 몇개의 라벨이 포함되어 있는지 count 정보 저장 필요. 이 기준으로 sorting 필요.
            label1_check = TbArtworkInfo.objects.filter(label1_id=label_dict["label_id"])
            label2_check = TbArtworkInfo.objects.filter(label2_id=label_dict["label_id"])
            label3_check = TbArtworkInfo.objects.filter(label3_id=label_dict["label_id"])
            if label_query:
                label_query = label_query.union(label1_check,label2_check,label3_check)
            else:
                label_query = label1_check.union(label2_check,label3_check)

        #TODO: order by 라벨이 많이 포함되어 있는 순으로 (count 정보)
        result_image_list = label_query.order_by("img_id").values("img_path","img_id")
        return result_image_list