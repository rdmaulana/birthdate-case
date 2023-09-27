import random
import string
import smtplib

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from twilio.rest import Client

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Twilio crendentials
TWILIO_SID = "your_twilio_sid"
TWILIO_AUTH_TOKEN = "your_twilio_auth_token"
TWILIO_PHONE_NUMBER = "your_twilio_phone_number"
USER_PHONE_NUMBER = "user_phone_number"  

# Email credentials
EMAIL_USER = "your_email@example.com"
EMAIL_PASSWORD = "your_email_password"

app = FastAPI()

# Simple in memory database for example purpose
users_db = []
promos_db = []
allowed_users_db = []

# User schema 
class User:
    def __init__(self, id, name, email, phone, birthdate, is_verified) -> None:
        self.id = id
        self.name = name
        self.email = email
        self.phone = phone
        self.birthdate = birthdate
        self.is_verified = is_verified

# Promo schema
class Promo:
    def __init__(self, id, code, start_date, end_date, rule, amount) -> None:
        self.id = id
        self.code = code
        self.start_date = start_date
        self.end_date = end_date
        self.rule = rule
        self.amount = amount

# Promo allowed user schema
class PromoAllowedUser:
    def __init__(self, id, promo_code_id, user_id) -> None:
        self.id = id
        self.promo_code_id = promo_code_id
        self.user_id = user_id

# Pydantic models for handle request n response data
class UserFilterField(BaseModel):
    email: str = None
    verifiedStatus: bool = None
    isBirthday: bool = None

class CreatePromoField(BaseModel):
    name: str
    startDate: datetime
    endDate: datetime
    amount: float
    validUsersID: list

# API 
@app.post("/fetchUsers")
async def fetch_users(filter_fields: UserFilterField):
    email = filter_fields.email
    verified_status = filter_fields.verifiedStatus
    is_birthday = filter_fields.isBirthday

    # Implement filtering based on the provided parameters
    filtered_users = []

    for user in users_db:
        if email and email.lower() != user.email.lower():
            continue
        if verified_status is not None and verified_status != user.is_verified:
            continue
        if is_birthday:
            today = datetime.now()
            if today.month == user.birthdate.month and today.day == user.birthdate.day:
                filtered_users.append(user)

    return [user.__dict__ for user in filtered_users]

@app.post("/generatePromoCode")
async def generate_promo_code(promo_data: CreatePromoField):
    name = promo_data.name
    start_date = promo_data.startDate
    end_date = promo_data.endDate
    amount = promo_data.amount
    valid_users_id = promo_data.validUsersID

    # Generate a random promo code
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

    # Create a new promo
    promo_id = len(promos_db) + 1
    promo = Promo(promo_id, code, start_date, end_date, "birthday", amount)
    promos_db.append(promo)

    # Add valid users for this promo
    for user_id in valid_users_id:
        promo_allowed_user_id = len(allowed_users_db) + 1
        allowed_user = PromoAllowedUser(promo_allowed_user_id, promo_id, user_id)
        allowed_users_db.append(allowed_user)

    return promo.__dict__

@app.post("/sendNotification")
async def send_notification(noti_data: dict):
    notification_type = noti_data.get('notificationType')
    subject = noti_data.get('subject')
    body = noti_data.get('body')
    target = noti_data.get('target')

    if notification_type == "email":
        send_email_notification(target, subject, body)
        return {"message": "Email notification sent successfully"}
    elif notification_type == "whatsapp":
        send_whatsapp_notification(target, body)
        return {"message": "WhatsApp notification sent successfully"}
    else:
        return {"message": "Invalid notification type"}

def send_email_notification(email_address, subject, body):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = email_address
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.example.com', 587)  # Replace with your SMTP server and port
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USER, email_address, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Error sending email: {str(e)}")

def send_whatsapp_notification(phone_number, message):
    try:
        client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
    except Exception as e:
        print(f"Error sending WhatsApp message: {str(e)}")