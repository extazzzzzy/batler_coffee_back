from fastapi import APIRouter, HTTPException
from app.models import VerifyRequest, AuthRequest
import bcrypt

def create_router(supabase):  # Переименовали функцию для ясности
    router = APIRouter()

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
    
    @router.post("/auth")
    async def auth(request: AuthRequest):
        input_code = request.input_code.encode('utf-8')
        verify_code = str(supabase.table("verify_codes") \
            .select("code") \
            .eq("phone_number", request.phone_number) \
            .execute().data[0]['code'])[2:-1].encode('utf-8')
        if not bcrypt.checkpw(input_code, verify_code): # Если введён неверный код
            return {"error": "false_code"}
        
        response = supabase.table("users") \
            .select("id") \
            .eq("phone_number", request.phone_number) \
            .execute()
        if not response.data:
            supabase.table("users").insert({
                "phone_number": request.phone_number,
            }).execute()
            return {"type_auth": "new_user"}
        else:

            return {"type_auth": "old_user"}
    return router

    