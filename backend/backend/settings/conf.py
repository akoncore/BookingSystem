#Project modules
from decouple import config

#------------------------------
#Env id
#
ENV_POSSIBLE_OPTIONS = [
    "local",
    "prod",
]
ENV_ID = config("BOOKING_ENV_ID",cast=str)

SECRET_KEY = config(
    "SECRET_KEY",
    default="django-insecure-b@wp(sggy#_@61*7gxq5-yxu)y54&t1w#f*f2dbkq(f0kc=1qo",
    cast=str,
)
