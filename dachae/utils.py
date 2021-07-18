import os
import json
import boto3
from boto3.s3.transfer import S3Transfer
from botocore.client import Config
from botocore.errorfactory import ClientError
import datetime

from .models import TbUserAuth,TbUserInfo,TbArtworkInfo,TbLabelInfo,TbProductInfo,TbCompanyInfo
import dachae.exceptions as exceptions

ARTWORK_LABEL_NUM = 3 #명화 1개당 라벨 개수
ARTWORK_BUCKET_NAME = os.getenv("ARTWORK_BUCKET_NAME")

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

    def save_file_into_s3(self,filepath,bucket,key):
        try:
            self.s3_client.put_object(Body=filepath,Bucket=bucket,Key=key)
        except:
            raise exceptions.StorageConnectionException
        return key

    def download_file(self,bucket,key,filepath):
        self.s3_client.download_file(bucket,key,filepath)
        return filepath
        
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

def get_public_url(bucket,key):
    public_url = "http://"+bucket+".s3.ap-northeast-2.amazonaws.com/"+key
    return public_url


def get_picture_detail_info(img_id):
    '''
    명화 1개의 상세정보 가져오기 (이미지 클릭 시 명화 상세정보 페이지로 이동)
    '''
    image_data = TbArtworkInfo.objects.filter(img_id=img_id).values("img_path","title","author","era","style","product_id","label1_id","label2_id","label3_id") #,"label4_id","label5_id")
    if image_data.exists():
        image_data = image_data[0]
        company_info = TbProductInfo.objects.filter(product_id=image_data["product_id"]).values("company_id","price")
        if company_info.exists():
            company_nm = TbCompanyInfo.objects.filter(company_id=company_info[0]["company_id"]).values("company_nm")
        else:
            raise exceptions.NoProductInfoException
        
        image_data.update(company_info[0])
        image_data.update(company_nm[0])
        del image_data["product_id"]
        del image_data["company_id"]
    else:
        raise exceptions.NoImageInfoException

    # 명화의 라벨 리스트 생성
    label_list = []
    for i in range(1,ARTWORK_LABEL_NUM+1):
        col_nm = "label"+str(i)+"_id"
        label_id = image_data[col_nm]
        del image_data[col_nm]

        if label_id is not None:
            try:
                label_nm = TbLabelInfo.objects.filter(label_id=label_id).values("label_nm")[0]
                label_list.append(label_nm["label_nm"])
            except:
                raise exceptions.DataBaseException

    image_data.update({
        "label_list":label_list
    })

    #s3 image path
    img_key = image_data["img_path"]
    public_url = get_public_url(ARTWORK_BUCKET_NAME,img_key)
    #response 를 위한 img path 데이터 변경
    image_data["img_path"]=public_url

    return image_data


def convert_recommended_img_path_into_s3_path(recommend_results):
    analog = recommend_results
    for i in range(len(analog)):
        img_id = analog[i]["img_id"]
        analog[i] = get_picture_detail_info(img_id)
    return analog

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
    ts = datetime.datetime.now() + datetime.timedelta(seconds=int(expires_in))
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
    #execRecommend
    if matching_result:
        analog = matching_result
        result_image_list = []
        for item in analog:
            count = 0
            for label_dict in label_list: 
                if TbArtworkInfo.objects.filter(img_id=item["img_id"],label1_id=label_dict["label_id"]).exists():
                    count += 1
                if TbArtworkInfo.objects.filter(img_id=item["img_id"],label2_id=label_dict["label_id"]).exists():
                    count += 1
                if TbArtworkInfo.objects.filter(img_id=item["img_id"],label3_id=label_dict["label_id"]).exists():
                    count += 1
            if count>0:
                result_image_list.append(
                    {
                        "img_id":item["img_id"],
                        "img_path":item["img_path"],
                        "count":count
                    }
                )
    #getPictureFilteredResult           
    else:
        #입력으로 받은 라벨 하나에 대해 해당 라벨을 포함하고 있는 artwork object들의 합집합
        label_query = None
        for label_dict in label_list: 
            #label1에 포함하고 있는지
            label1_check = TbArtworkInfo.objects.filter(label1_id=label_dict["label_id"])
            label1_obj = [{'img_id':obj.img_id,'img_path':obj.img_path} for obj in label1_check]
            #label2에 포함하고 있는지
            label2_check = TbArtworkInfo.objects.filter(label2_id=label_dict["label_id"])
            label2_obj = [{'img_id':obj.img_id,'img_path':obj.img_path} for obj in label2_check]
            #label3에 포함하고 있는지
            label3_check = TbArtworkInfo.objects.filter(label3_id=label_dict["label_id"])
            label3_obj = [{'img_id':obj.img_id,'img_path':obj.img_path} for obj in label3_check]

            if label_query:
                label_query += label1_obj+label2_obj+label3_obj
            else:
                label_query = label1_obj+label2_obj+label3_obj
        
        result_label_query = label_query
        #중복제거 및 count 정보 추출
        result_image_list = []
        while result_label_query:
            item = result_label_query[0]
            count = result_label_query.count(item)
            result_image_list.append(
                {
                    "img_id":item["img_id"],
                    "img_path":item["img_path"],
                    "count":count
                }
            )
            result_label_query = [value for value in result_label_query if value != item]

    #count 기준으로 정렬
    result_image_list = sorted(result_image_list,key=lambda k:k["count"],reverse=True)
    return result_image_list