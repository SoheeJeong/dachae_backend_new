from rest_framework.views import exception_handler

def handle_exception(exception_message, context):
    response = exception_handler(exception_message, context)

    if response is not None:
        response.data['msg_id'] = ""
        response.data['msg_desc'] = str(exception_message)
        del response.data['detail']

    return response