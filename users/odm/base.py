from nwodm.schemas import BaseAnnotationSchema


class UserAnnotationSchema(BaseAnnotationSchema):
    """Override base schema with microservice's validation error code."""

    validation_error_code: str = 'NB-ERROR-00402'
