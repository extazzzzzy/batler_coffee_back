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
    created_at_token: str
    name: str
    birthday: str

class UseOnlyTokenRequest(BaseModel):
    token: str
    created_at_token: str

class CreateOrderRequest(BaseModel):
    token: str
    created_at_token: str
    ready_for: str
    description: str
    total_sum: str

class CheckPromocodeRequest(BaseModel):
    token: str
    created_at_token: str
    promocode: str
    total_sum: str

# ТОЛЬКО АДМИНСКИЕ МОДЕЛИ ⬇️⬇️⬇️
class SignUpNewAdmin(BaseModel):
    token: str
    created_at_token: str
    login: str
    secret_key: str
    name: str

class SignInAdmin(BaseModel):
    login: str
    secret_key: str

class EditProductsIngredients(BaseModel):
    token: str
    created_at_token: str
    product_id: int
    ingredient_id: int
    type_edit: str # create/delete

class DeleteProduct(BaseModel):
    token: str
    created_at_token: str
    product_id: int

class CreateProduct(BaseModel):
    token: str
    created_at_token: str
    name: str
    description: str
    composition: str
    price: str
    base64_img: str
    protein: str
    fats: str
    carbohydrates: str
    weight: str
    kilocalories: str