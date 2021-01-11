from rest_framework.exceptions import APIException


class InvalidPasswordException(APIException):
    status_code = 401
    default_detail = "Password가 다릅니다. 확인 후 재입력하세요."


class InvalidIdException(APIException):
    status_code = 401
    default_detail = "ID가 일치하지 않습니다. 확인 후 재입력하세요."


class InvalidPasswordFiveTimesException(APIException):
    status_code = 401
    default_detail = "Password 오류가 5회 이상입니다. 관리자에게 문의하세요."


class UnconnectedException(APIException):
    status_code = 401
    default_detail = "해당 계정은 3개월 이상 미접속하여 휴면상태가 되었습니다. 관리자에게 문의하세요."


class LeftMemberException(APIException):
    status_code = 401
    default_detail = "탈퇴한 회원입니다."


class NotSamePasswordException(APIException):
    status_code = 500
    default_detail = "새로운 비밀번호와 확인 비밀번호가 일치하지 않습니다."


class SamePasswordWhenBeforeException(APIException):
    status_code = 500
    default_detail = "변경하실 비밀번호가 이전과 같습니다."


class NotSpecialCharException(APIException):
    status_code = 500
    default_detail = "비밀번호에 특수문자 1개 이상 포함하여야 합니다."

class SameAsExistingDatasetName(APIException):
    status_code = 500
    default_detail = '이미 존재하는 Dataset name입니다.'

class InvalidTokenException(APIException):
    status_code = 401
    default_detail = "Token이 유효하지 않습니다."


class InvalidAccessTokenException(APIException):
    status_code = 500
    default_detail = "Access Token이 유효하지 않습니다."


class ExpirationAccessTokenException(APIException):
    status_code = 401
    default_detail = "Access Token이 만료됐습니다. Token을 갱신하거나 로그인을 다시 해주세요."


class ExpirationRefreshTokenException(APIException):
    status_code = 401
    default_detail = "Refresh Token이 만료됐습니다. 로그인을 다시 해주세요."


class NotTokenInfoException(APIException):
    status_code = 401
    default_detail = "로그인을 다시 해주세요."


class NotAdminException(APIException):
    status_code = 500
    default_detail = "Admin이 아닙니다."


class NotDeveloperException(APIException):
    status_code = 500
    default_detail = "Developer가 아닙니다."


class ExistConflictException(APIException):
    status_code = 500
    default_detail = "중복된 이름입니다. 다른 이름으로 만들어주세요."


class DataBaseException(APIException):
    status_code = 500
    default_detail = "Database Error"


class IntegrityException(APIException):
    status_code = 500
    default_detail = "Integrity Error"


class NotAuthGroup(APIException):
    status_code = 500
    default_detail = "본인이 생성한 그룹만 상태 변경할 수 있습니다."