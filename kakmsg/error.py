from marshmallow import Schema, fields
import marshmallow

class Error(object):
    def __init__(self, error_code=None, message=None):
        self.error_code = error_code
        self.message = message

class ErrorSchema(Schema):
    error_code = fields.Int(missing=None)
    message = fields.Str(missing=None)

    @marshmallow.post_load
    def make_error(self, data):
        return Error(**data)
