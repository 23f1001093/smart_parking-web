from dotenv import load_dotenv
load_dotenv()

import os
print("MAIL_USERNAME:", repr(os.environ.get("MAIL_USERNAME")))
print("MAIL_PASSWORD:", repr(os.environ.get("MAIL_PASSWORD")))
print("MAIL_SERVER:", repr(os.environ.get("MAIL_SERVER")))
