import os

# AWS_STORAGE_BUCKET_NAME = "metapeering"
# AWS_ACCESS_KEY_ID = "AKIASYCTCIIFWQ2IRN45"
# AWS_SECRET_ACCESS_KEY = "0+6Z4DlgKBZzdG+1rJcGZFQd2VbsP0vcL/Xe2Cb2"
# DATABASE_URI = "sqlite:///db.sqlite3"
# USER1_PW = "dumy"
# USER2_PW = "dummy"
# USER3_PW = "dummmy"
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
DATABASE_URI = 'sqlite:///db.sqlite3'
USER1_PW = os.environ.get("USER1_PW")
USER2_PW = os.environ.get("USER2_PW")
USER3_PW = os.environ.get("USER3_PW")
