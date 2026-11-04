import textlocal.exceptions


class Response(object):
    def __init__(self, json):
        if json["status"] is not "success":
            error = json["errors"][0]
            raise textlocal.exceptions.TextlocalException(error.get("message"))
