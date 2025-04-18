from pydantic import BaseModel

# Модель для входящих данных при авторизации (для таблицы verify_codes)
class VerifyRequest(BaseModel):
    phone_number: str  # Формат: "+79123456789"
    type_auth: str

class AuthRequest(BaseModel):
    phone_number: str
    input_code: str

class UserDataRequest(BaseModel):
    token: str
    name: str
    birthday: str

class UseOnlyTokenRequest(BaseModel):
    token: str

class CreateOrderRequest(BaseModel):
    token: str
    ready_for: str
    description: str
    total_sum: str

class CheckPromocodeRequest(BaseModel):
    token: str
    promocode: str
    total_sum: str