from fastapi import APIRouter, HTTPException, status
from app.models import VerifyRequest, AuthRequest, UserDataRequest, UseOnlyTokenRequest
import bcrypt
import os
from jose import jwt
from dotenv import load_dotenv
from hashlib import sha256

load_dotenv()

# параметры авторизации
SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITM = "HS256"

def create_router(supabase):
    router = APIRouter()

    # Второстепенные методы
    def create_jwt_token(user_id: str) -> str:
        return jwt.encode({"sub": user_id}, SECRET_KEY, algorithm=ALGORITM)

    def is_existing_token(request):
        response = supabase.table("personal_access_tokens") \
            .select("id") \
            .eq("token", str(sha256(request.token.encode('utf-8')).hexdigest())) \
            .execute()
        if not response.data:
            return False
        return True
    
    def hash_token(token):
        return str(sha256(token.encode('utf-8')).hexdigest())

    # Маршруты
    # Маршрут для авторизации через телеграм
    @router.post("/verify_tg")
    async def verify_phone(request: VerifyRequest): # Метод начала авторизации для любого способа (он передаётся в запросе)
        try:
            # Удаляем старые коды
            supabase.table("verify_codes") \
                .delete() \
                .eq("phone_number", request.phone_number) \
                .execute()

            # Генерируем и создаём новую запись о авторизации
            supabase.table("verify_codes").insert({
                "phone_number": request.phone_number,
                "type_auth": request.type_auth
            }).execute()

            return {"status": "success"}
            
        except Exception as e:
            raise HTTPException(500, detail=str(e))

    # Маршрут для подтверждения кода и входа
    @router.post("/auth")
    async def auth(request: AuthRequest):
        # Проверка правильности кода
        input_code = request.input_code.encode('utf-8')
        verify_code = str(supabase.table("verify_codes") \
            .select("code") \
            .eq("phone_number", request.phone_number) \
            .execute().data[0]['code'])[2:-1].encode('utf-8')
        if not bcrypt.checkpw(input_code, verify_code): 
            return {"error": "false_code"}
        
        # Удаляем код после входа
        supabase.table("verify_codes") \
                .delete() \
                .eq("phone_number", request.phone_number) \
                .execute()
        
        # Продолжение процесса авторизации
        user = supabase.table("users") \
            .select("id") \
            .eq("phone_number", request.phone_number) \
            .maybe_single() \
            .execute()
        # Проверка есть юзер или нет
        if not user or not user.data:
            user = supabase.table("users") \
                .insert({"phone_number": request.phone_number}) \
                .execute()
            user_id = user.data[0]['id']
            is_new = True
        else:
            user_id = user.data['id']
            is_new = False
        
        # Создаём токен и заносим в БД
        token = create_jwt_token(user_id)
        supabase.table("personal_access_tokens") \
            .upsert({
                "user_id": user_id,
                "token": hash_token(token)
            }, on_conflict="user_id") \
            .execute()
        
        return {
            "access_token": token,
            "user_id": user_id,
            "is_new_user": is_new
        }
    
    # Маршрут для изменения пользовательских данных
    @router.post("/save_userdata")
    # Изменение имени и дня рождения пользователя
    async def save_userdata(request: UserDataRequest):
        if not is_existing_token(request):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        user_id = (supabase.table("personal_access_tokens") \
            .select("user_id") \
            .eq("token", hash_token(request.token)) \
            .execute()).data[0]['user_id']
        supabase.table("users") \
            .update({"name": request.name, "birthday": request.birthday}) \
            .eq("id", user_id) \
            .execute()
        
        return {
            "status": "access"
        }

    # Маршрут для получения пользовательских данных
    @router.post("/fetch_userdata")
    # Изменение имени и дня рождения пользователя
    async def fetch_userdata(request: UseOnlyTokenRequest):
        if not is_existing_token(request):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        user_id = (supabase.table("personal_access_tokens") \
            .select("user_id") \
            .eq("token", hash_token(request.token)) \
            .execute()).data[0]['user_id']
        name = (supabase.table("users") \
            .select("name") \
            .eq("id", user_id) \
            .execute()).data[0]['name']
        birthday = (supabase.table("users") \
            .select("birthday") \
            .eq("id", user_id) \
            .execute()).data[0]['birthday']
        
        return {
            "name": name,
            "birthday": birthday,
        }
    # Маршрут для получения информации о действительности токена
    @router.post("/check_validate_token")
    async def check_validate_token(request: UseOnlyTokenRequest):
        if (is_existing_token(request)):
            return {
                "validate": True
            }
        return {
            "validate": False
        }

    return router

    