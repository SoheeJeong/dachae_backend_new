from rest_framework.exceptions import APIException


class NewMemberException(APIException):
    status_code = 401
    default_detail = "가입된 회원 정보가 없습니다. 회원가입 해주세요."


class DormantMemberException(APIException):
    status_code = 401
    default_detail = "해당 계정은 3개월 이상 미접속하여 휴면상태가 되었습니다. 관리자에게 문의하세요."


class LeftMemberException(APIException):
    status_code = 401
    default_detail = "탈퇴한 회원입니다."

class InvalidUserIdException(APIException):
    status_code = 401
    default_detail = "해당 id와 일치하는 회원정보가 없습니다."

class InvalidAccessTokenException(APIException):
    status_code = 500
    default_detail = "Access Token이 유효하지 않습니다."


class ExpiredAccessTokenException(APIException):
    status_code = 401
    default_detail = "Access Token이 만료되었습니다."


class ExpirationRefreshTokenException(APIException):
    status_code = 401
    default_detail = "Refresh Token이 만료되었습니다. 다시 로그인해주세요."


class NotTokenInfoException(APIException):
    status_code = 401
    default_detail = "다시 로그인해주세요."

class ParameterMissingException(APIException):
    status_code = 401
    default_detail = "필요한 parameter 가 전달되지 않았습니다."

class NoCompanyInfoException(APIException):
    status_code = 401
    default_detail = "해당 이미지의 판매처 정보가 존재하지 않습니다."

class NoProductInfoException(APIException):
    status_code = 401
    default_detail = "해당 상품에 대한 정보가 존재하지 않습니다."

class NoImageInfoException(APIException):
    status_code = 401
    default_detail = "해당 이미지에 대한 정보가 존재하지 않습니다."

class StorageConnectionException(APIException):
    status_code = 500
    default_detail = "스토리지로부터 파일을 가져오는 데 실패했습니다."


class NotAdminException(APIException):
    status_code = 500
    default_detail = "관리자가 아닙니다."


class NotMemberException(APIException):
    status_code = 500
    default_detail = "맴버가 아닙니다."


class DataBaseException(APIException):
    status_code = 500
    default_detail = "Database Error"


class AlreadyInWishlistException(APIException):
    status_code = 403
    default_detail = "이미 위시리스트에 있는 항목입니다."

class NotInWishlistException(APIException):
    status_code = 403
    default_detail = "위시리스트에 없는 항목입니다. 삭제할 수 없습니다."


class NoFileUploadedException(APIException):
    status_code = 403
    default_detail = "업로드된 사진이 없습니다."

class TooManyFileUploadedException(APIException):
    status_code = 403
    default_detail = "사진을 1장만 업로드해주세요."

class WrongFileFormatException(APIException):
    status_code = 403
    default_detail = "허용되는 파일 형식이 아닙니다."

class TooMuchLabelSeletedException(APIException):
    status_code = 403
    default_detail = "선택된 라벨이 너무 많습니다."