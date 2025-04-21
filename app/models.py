from pydantic import BaseModel
from typing import Optional

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

class DeleteIngredient(BaseModel):
    token: str
    created_at_token: str
    ingredient_id: int

class DeletePromocode(BaseModel):
    token: str
    created_at_token: str
    promocode_id: int

class CreateProduct(BaseModel):
    token: str
    created_at_token: str
    name: str
    description: str
    composition: str
    is_available: bool
    price: str
    base64_img: str
    protein: str
    fats: str
    carbohydrates: str
    weight: str
    kilocalories: str

class CreateIngredient(BaseModel):
    token: str
    created_at_token: str
    name: str
    price: str

class CreatePromocode(BaseModel):
    token: str
    created_at_token: str
    promocode: str
    description: str
    is_active: bool
    discount: str
    min_total_sum: str
    is_percent: bool
    base64_img: str


class UpdateProduct(BaseModel):
    token: str
    created_at_token: str
    product_id: int
    promocode: Optional[str] = None
    description: Optional[str] = None
    composition: Optional[str] = None
    is_available: Optional[bool] = None
    price: Optional[str] = None
    base64_img: Optional[str] = None
    protein: Optional[str] = None
    fats: Optional[str] = None
    carbohydrates: Optional[str] = None
    weight: Optional[str] = None
    kilocalories: Optional[str] = None

class UpdatePromocode(BaseModel):
    token: str
    created_at_token: str
    promocode_id: int
    promocode: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    discount: Optional[str] = None
    min_total_sum: Optional[str] = None
    base64_img: Optional[str] = None
    is_percent: Optional[bool] = None

class UpdateIngredient(BaseModel):
    token: str
    created_at_token: str
    ingredient_id: int
    name: Optional[str] = None
    price: Optional[str] = None

class UpdateOrder(BaseModel):
    token: str
    created_at_token: str
    order_id: int
    ready_for: Optional[str] = None
    description: Optional[str] = None
    total_sum: Optional[str] = None
    status: Optional[str] = None

class DeleteAdministrator(BaseModel):
    token: str
    created_at_token: str
    user_id: int
