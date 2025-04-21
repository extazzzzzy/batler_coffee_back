from fastapi import APIRouter, HTTPException, status

from app.models import VerifyRequest, AuthRequest, UserDataRequest, UseOnlyTokenRequest, \
      CreateOrderRequest, CheckPromocodeRequest, SignUpNewAdmin, SignInAdmin, EditProductsIngredients, \
      DeleteProduct, CreateProduct, UpdateProduct, DeleteIngredient, CreateIngredient, UpdateIngredient, \
      DeletePromocode, CreatePromocode, UpdatePromocode

import os
from jose import jwt
from dotenv import load_dotenv
from hashlib import sha256
from datetime import datetime, timedelta
from passlib.hash import bcrypt
import base64
import uuid
from urllib.parse import urlparse

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
            .eq("created_at", request.created_at_token) \
            .execute()
        if not response.data:
            return False
        return True
    
    def is_existing_token_admin(request):
        response = supabase.table("personal_access_tokens") \
            .select("id") \
            .eq("token", str(sha256(request.token.encode('utf-8')).hexdigest())) \
            .eq("created_at", request.created_at_token) \
            .execute()
        if not response.data:
            return False
        
        user_id = (supabase.table("personal_access_tokens") \
            .select("user_id") \
            .eq("token", hash_token(request.token)) \
            .execute()).data[0]['user_id']
        role = (supabase.table("users") \
            .select("role") \
            .eq("id", user_id) \
            .execute()).data[0]['role']
        if role != 1:
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
        if not bcrypt.verify(input_code.decode(), verify_code.decode()): 
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
            .delete() \
            .eq("user_id", user_id) \
            .execute()
        supabase.table("personal_access_tokens").insert({
            "user_id": user_id,
            "token": hash_token(token),
        }).execute()
        created_at_token = str(supabase.table("personal_access_tokens") \
            .select("created_at") \
            .eq("token", hash_token(token)) \
            .execute().data[0]['created_at'])
        
        return {
            "access_token": token,
            "user_id": user_id,
            "is_new_user": is_new,
            "created_at_token": created_at_token,
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
        role = (supabase.table("users") \
            .select("role") \
            .eq("id", user_id) \
            .execute()).data[0]['role']
        
        return {
            "name": name,
            "birthday": birthday,
            "role": role,
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
    
    # Маршрут для отзыва токена (выход)
    @router.delete("/out")
    async def out_token(request: UseOnlyTokenRequest):
        if not is_existing_token(request):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        
        try:
            supabase.table("personal_access_tokens") \
                .delete() \
                .eq("token", hash_token(request.token)) \
                .execute()
            return {"out_token": "success"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
    # Маршрут для получения меню (с ингредиентами)
    @router.get("/fetch_products")
    async def fetch_products():
        try:
            products_response = supabase.table("products").select("*").execute()
            products = products_response.data

            if not products:
                raise HTTPException(status_code=404, detail="Продукты отсутствуют")

            links_response = supabase.table("products_to_ingredients") \
                .select("product_id, ingredients!inner(id, name, price)") \
                .execute()
            
            links = links_response.data

            ingredients_by_product = {}
            for link in links:
                product_id = link["product_id"]
                if product_id not in ingredients_by_product:
                    ingredients_by_product[product_id] = []
                ingredients_by_product[product_id].append(link["ingredients"])

            result = []
            for product in products:
                product_with_ingredients = {
                    **product,
                    "ingredients": ingredients_by_product.get(product["id"], [])
                }
                result.append(product_with_ingredients)
            
            return {
                "status": "success",
                "products": result
            }
        
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка получения продуктов: {str(e)}"
            )
        
    # Маршрут для создания нового заказа
    @router.post("/create_order")
    async def create_order(request: CreateOrderRequest):
        if not is_existing_token(request):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            user_id = (supabase.table("personal_access_tokens") \
                .select("user_id") \
                .eq("token", hash_token(request.token)) \
                .execute()).data[0]['user_id']
            supabase.table("orders").insert({
                "user_id": user_id,
                "ready_for": request.ready_for,
                "description": request.description,
                "total_sum": request.total_sum,
            }).execute()
            return {
                "status": "success"
            }
        
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка создания заказа: {str(e)}"
            )
    
    # Маршрут для проверки валидности промокода
    @router.post("/check_promocode")
    async def check_promocode(request: CheckPromocodeRequest):
        if not is_existing_token(request):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            response = (supabase.table("promocodes") \
                .select("*") \
                .eq("promocode", request.promocode) \
                .execute())
            if not response.data:
                raise HTTPException(status_code=404, detail="Промокод не найден")
            
            is_active_promocode = response.data[0]['is_active']
            if is_active_promocode == False:
                raise HTTPException(status_code=404, detail="Промокод неактивен")
            
            user_id = (supabase.table("personal_access_tokens") \
                .select("user_id") \
                .eq("token", hash_token(request.token)) \
                .execute()).data[0]['user_id']
            birthday_user = (supabase.table("users") \
                .select("birthday") \
                .eq("id", user_id) \
                .execute()).data[0]['birthday']

            # Проверка на промокод ДР, что он действителен только 3 дня ДО и 3 дня ПОСЛЕ
            if request.promocode == "ДР":
                today = datetime.now().date()

                birthday_str = birthday_user
                day, month, year = map(int, birthday_str.split('.'))
                birthday = datetime(year=datetime.now().year, month=month, day=day).date()

                if birthday < today:
                    birthday = datetime(year=datetime.now().year + 1, month=month, day=day).date()

                start_date = birthday - timedelta(days=3)
                end_date = birthday + timedelta(days=3)

                if (start_date <= today <= end_date) == False:
                    raise HTTPException(status_code=404, detail="Промокод неактивен для данного пользователя")

            discount = int(response.data[0]['discount'])
            min_total_sum = int(response.data[0]['min_total_sum'])
            is_percent = response.data[0]['is_percent']
            total_sum = int(request.total_sum)
            
            if (total_sum >= min_total_sum):
                if is_percent:
                    new_sum = total_sum * (1 - discount / 100)
                else:
                    new_sum = total_sum - discount
                return {
                    "status": "success",
                    "message": "Промокод активен",
                    "new_sum": int(new_sum)
                }
            
            raise HTTPException(status_code=404, detail="Выполнены не все условия акции") 
        
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка проверки промокода: {str(e)}"
            )

    # Маршрут для получения заказов пользователя
    @router.post("/fetch_user_orders")
    async def fetch_user_orders(request: UseOnlyTokenRequest):
        if not is_existing_token(request):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        user_id = (supabase.table("personal_access_tokens") \
            .select("user_id") \
            .eq("token", hash_token(request.token)) \
            .execute()).data[0]['user_id']
        try:
            orders_response = supabase.table("orders") \
                .select("*") \
                .eq("user_id", user_id) \
                .order("created_at", desc=True) \
                .execute()
            orders = orders_response.data
            formatted_orders = []
            for order in orders:
                formatted_orders.append({
                    "order_id": order["id"],
                    "created_at": order["created_at"],
                    "ready_for": order["ready_for"],
                    "description": order["description"],
                    "total_sum": order["total_sum"],
                    "status": order["status"]
                })
            
            return {
                "success": True,
                "orders": formatted_orders,
                "count": len(orders)
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при получении заказов: {str(e)}"
            )
    # Маршрут для получения акций (промокодов)
    @router.get("/fetch_promocodes")
    async def fetch_promocodes():
        try:
            promocodes_response = supabase.table("promocodes") \
                .select("*") \
                .order("created_at", desc=True) \
                .execute()
            promocodes = promocodes_response.data
            formatted_promocodes = []
            for promocode in promocodes:
                if promocode['is_active'] == True:
                    formatted_promocodes.append({
                        "promocode_id": promocode["id"],
                        "promocode": promocode["promocode"],
                        "description": promocode["description"],
                        "src_img": promocode["src_img"],
                        "is_acitve": promocode["is_active"],
                    })
            
            return {
                "success": True,
                "orders": formatted_promocodes,
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при получении заказов: {str(e)}"
            )
    
    # ТОЛЬКО АДМИНСКИЕ МАРШРУТЫ ⬇️⬇️⬇️
    # Маршрут для регистрации нового администратора
    @router.post("/signup_admin")
    async def signup_admin(request: SignUpNewAdmin):
        if not is_existing_token_admin(request):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        hashed_secretkey = bcrypt.hash(request.secret_key)
        try:
            supabase.table("users").insert({
                "phone_number": request.login,
                "secret_key": hashed_secretkey,
                "name": request.name,
                "role": 1,
            }).execute()
            return {
                "status": "success",
                "message": "Администратор создан",
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка регистрации: {str(e)}"
            )
        
    # Маршрут для авторизации администратора
    @router.post("/signin_admin")
    async def signin_admin(request: SignInAdmin):
        user_response = (supabase.table("users") \
            .select("*") \
            .eq("phone_number", request.login) \
            .execute())
        if not user_response.data:
            raise HTTPException(
                status_code=404,
                detail="Администратора с таким логином не существует"
            )
        
        user_data = user_response.data[0]
        user_id = user_data['id']
        stored_hash = user_data['secret_key']

        if not bcrypt.verify(request.secret_key, stored_hash):
            raise HTTPException(401, "Неверный пароль")
        
        if user_data['role'] != 1:
            raise HTTPException(401, "Недостаточно прав")
        
        # Создаём токен и заносим в БД
        token = create_jwt_token(user_id)

        supabase.table("personal_access_tokens") \
            .delete() \
            .eq("user_id", user_id) \
            .execute()
        supabase.table("personal_access_tokens").insert({
            "user_id": user_id,
            "token": hash_token(token),
        }).execute()
        created_at_token = str(supabase.table("personal_access_tokens") \
            .select("created_at") \
            .eq("token", hash_token(token)) \
            .execute().data[0]['created_at'])
        
        return {
            "access_token": token,
            "created_at_token": created_at_token,
        }
    
    # Маршрут для создания/удаления ингредиентов у продукта
    @router.post("/edit_products_ingredients")
    async def edit_products_ingredients(request: EditProductsIngredients):
        if not is_existing_token_admin(request):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            if request.type_edit == "create":
                supabase.table("products_to_ingredients").insert({
                    "product_id": request.product_id,
                    "ingredient_id": request.ingredient_id,
                }).execute()
                return {
                    "message": "Ингредиент успешно добавлен"
                }

            elif request.type_edit == "delete":
                supabase.table("products_to_ingredients") \
                    .delete() \
                    .eq("product_id", request.product_id) \
                    .eq("ingredient_id", request.ingredient_id) \
                .execute()
                return {
                    "message": "Ингредиент успешно удалён"
                }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка редактирования: {str(e)}"
            )

    # Маршрут для удаления продукта
    @router.delete("/delete_product")
    async def delete_product(request: DeleteProduct):
        if not is_existing_token_admin(request):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            product = supabase.table("products") \
                .select("src_img") \
                .eq("id", request.product_id) \
                .execute()
            if not product.data:
                raise HTTPException(status_code=404, detail="Продукт не найден")
            src_img = product.data[0]['src_img']

            try:
                supabase.table("products_to_ingredients") \
                    .delete() \
                    .eq("product_id", request.product_id) \
                    .execute()
            except Exception as links_error:
                print(f"Ошибка удаления связей с ингредиентами: {str(links_error)}")

            supabase.table("products") \
                .delete() \
                .eq("id", request.product_id) \
                .execute()
            
            try:
                filename = os.path.basename(src_img)
                full_path = os.path.join("app/src/img/menu/", filename)
                if os.path.exists(full_path):
                    os.remove(full_path)
            except Exception as img_error:
                print(f"Ошибка удаления изображения: {str(img_error)}")
            
            return {
                "message": "Продукт успешно удалён",
                "deleted_image": bool(src_img)
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка удаления: {str(e)}"
            )
    
    # Маршрут для создания продукта
    @router.post("/create_product")
    async def create_product(request: CreateProduct):
        if not is_existing_token_admin(request):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            # ОБРАБОТКА ИЗОБРАЖЕНИЯ ИЗ BASE64
            base64_img = request.base64_img
            if ',' in base64_img:
                base64_img = base64_img.split(',')[1]
            img_data = base64.b64decode(base64_img)
            filename = f"{uuid.uuid4()}.jpg"
            filepath = os.path.join("app/src/img/menu/", filename)
            with open(filepath, "wb") as f:
                f.write(img_data)
            src_img = str(os.getenv("PATH_IMG")) + "menu/" + str(filename)

            supabase.table("products").insert({
                    "name": request.name,
                    "description": request.description,
                    "composition": request.composition,
                    "is_available": request.is_available,
                    "price": request.price,
                    "src_img": src_img,
                    "protein": request.protein,
                    "fats": request.fats,
                    "carbohydrates": request.carbohydrates,
                    "weight": request.weight,
                    "kilocalories": request.kilocalories
            }).execute()

            return {
                "message": "Продукт успешно создан"
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка создания: {str(e)}"
            )
    
    # Маршрут для обновления данных о продукте
    @router.post("/update_product")
    async def update_product(request: UpdateProduct):
        if not is_existing_token_admin(request):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        
        try:
            update_data = {}
            
            if request.name is not None:
                update_data["name"] = request.name
            if request.description is not None:
                update_data["description"] = request.description
            if request.composition is not None:
                update_data["composition"] = request.composition
            if request.is_available is not None:
                update_data["is_available"] = request.is_available
            if request.price is not None:
                update_data["price"] = request.price
            if request.protein is not None:
                update_data["protein"] = request.protein
            if request.fats is not None:
                update_data["fats"] = request.fats
            if request.carbohydrates is not None:
                update_data["carbohydrates"] = request.carbohydrates
            if request.weight is not None:
                update_data["weight"] = request.weight
            if request.kilocalories is not None:
                update_data["kilocalories"] = request.kilocalories
            
            if request.base64_img is not None:
                # удаление старого изображения с сервера
                product = supabase.table("products") \
                    .select("src_img") \
                    .eq("id", request.product_id) \
                    .execute()
                src_img = product.data[0]['src_img']

                try:
                    filename = os.path.basename(src_img)
                    full_path = os.path.join("app/src/img/menu/", filename)
                    if os.path.exists(full_path):
                        os.remove(full_path)
                except Exception as img_error:
                    print(f"Ошибка удаления изображения: {str(img_error)}")
                
                # создание нового изображения
                base64_img = request.base64_img
                if ',' in base64_img:
                    base64_img = base64_img.split(',')[1]
                img_data = base64.b64decode(base64_img)
                filename = f"{uuid.uuid4()}.jpg"
                filepath = os.path.join("app/src/img/menu/", filename)
                with open(filepath, "wb") as f:
                    f.write(img_data)
                src_img = str(os.getenv("PATH_IMG")) + "menu/" + str(filename)
                update_data["src_img"] = src_img
            
            # Обновляем только если есть что обновлять
            if update_data:
                supabase.table("products").update(update_data).eq("id", request.product_id).execute()
            
            return {
                "message": "Продукт успешно обновлен"
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка обновления: {str(e)}"
            )
        
    # Маршрут для получения всех ингредиентов
    @router.get("/fetch_ingredients")
    async def fetch_ingredients():
        try:
            ingredients_response = supabase.table("ingredients") \
                .select("*") \
                .execute()
            ingredients = ingredients_response.data
            formatted_ingredients = []
            for ingredient in ingredients:
                formatted_ingredients.append({
                    "id": ingredient["id"],
                    "name": ingredient["name"],
                    "price": ingredient["price"],
                })
            
            return {
                "success": True,
                "ingredients": formatted_ingredients,
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при получении ингредиентов: {str(e)}"
            )
        
    # Маршрут для удаления ингредиента
    @router.delete("/delete_ingredient")
    async def delete_ingredient(request: DeleteIngredient):
        if not is_existing_token_admin(request):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            try:
                supabase.table("products_to_ingredients") \
                    .delete() \
                    .eq("ingredient_id", request.ingredient_id) \
                    .execute()
            except Exception as links_error:
                print(f"Ошибка удаления связей с ингредиентами: {str(links_error)}")

            supabase.table("ingredients") \
                .delete() \
                .eq("id", request.ingredient_id) \
                .execute()
            
            return {
                "message": "Ингредиент успешно удалён",
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка удаления: {str(e)}"
            )

    # Маршрут для создания ингредиента
    @router.post("/create_ingredient")
    async def create_ingredient(request: CreateIngredient):
        if not is_existing_token_admin(request):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            supabase.table("ingredients").insert({
                    "name": request.name,
                    "price": request.price,
            }).execute()

            return {
                "message": "Ингредиент успешно создан"
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка создания: {str(e)}"
            )
    
    # Маршрут для обновления данных о ингредиенте
    @router.post("/update_ingredient")
    async def update_ingredient(request: UpdateIngredient):
        if not is_existing_token_admin(request):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        
        try:
            update_data = {}
            
            if request.name is not None:
                update_data["name"] = request.name
            if request.price is not None:
                update_data["price"] = request.price
            
            # Обновляем только если есть что обновлять
            if update_data:
                supabase.table("ingredients").update(update_data).eq("id", request.ingredient_id).execute()
            
            return {
                "message": "Ингредиент успешно обновлен"
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка обновления: {str(e)}"
            )
        
    # Маршрут для удаления промокода
    @router.delete("/delete_promocode")
    async def delete_promocode(request: DeletePromocode):
        if not is_existing_token_admin(request):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            supabase.table("promocodes") \
                .delete() \
                .eq("id", request.promocode_id) \
                .execute()
            
            return {
                "message": "Промокод успешно удалён",
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка удаления: {str(e)}"
            )
        
    # Маршрут для создания промоакции
    @router.post("/create_promocode")
    async def create_promocode(request: CreatePromocode):
        if not is_existing_token_admin(request):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            # ОБРАБОТКА ИЗОБРАЖЕНИЯ ИЗ BASE64
            base64_img = request.base64_img
            if ',' in base64_img:
                base64_img = base64_img.split(',')[1]
            img_data = base64.b64decode(base64_img)
            filename = f"{uuid.uuid4()}.jpg"
            filepath = os.path.join("app/src/img/promo/", filename)
            with open(filepath, "wb") as f:
                f.write(img_data)
            src_img = str(os.getenv("PATH_IMG")) + "promo/" + str(filename)

            supabase.table("promocodes").insert({
                    "promocode": request.promocode,
                    "description": request.description,
                    "is_active": request.is_active,
                    "discount": request.discount,
                    "min_total_sum": request.min_total_sum,
                    "is_percent": request.is_percent,
                    "src_img": src_img,
            }).execute()

            return {
                "message": "Промокод успешно создан"
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка создания: {str(e)}"
            )
    
    # Маршрут для обновления данных о промоакции
    @router.post("/update_promocode")
    async def update_promocode(request: UpdatePromocode):
        if not is_existing_token_admin(request):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        
        try:
            update_data = {}
            
            if request.name is not None:
                update_data["name"] = request.name
            if request.description is not None:
                update_data["description"] = request.description
            if request.is_active is not None:
                update_data["is_active"] = request.is_active
            if request.discount is not None:
                update_data["discount"] = request.discount
            if request.min_total_sum is not None:
                update_data["min_total_sum"] = request.min_total_sum
            if request.is_percent is not None:
                update_data["is_percent"] = request.is_percent
            
            if request.base64_img is not None:
                # удаление старого изображения с сервера
                product = supabase.table("promocodes") \
                    .select("src_img") \
                    .eq("id", request.promocode_id) \
                    .execute()
                src_img = product.data[0]['src_img']

                try:
                    filename = os.path.basename(src_img)
                    full_path = os.path.join("app/src/img/promo/", filename)
                    if os.path.exists(full_path):
                        os.remove(full_path)
                except Exception as img_error:
                    print(f"Ошибка удаления изображения: {str(img_error)}")
                
                # создание нового изображения
                base64_img = request.base64_img
                if ',' in base64_img:
                    base64_img = base64_img.split(',')[1]
                img_data = base64.b64decode(base64_img)
                filename = f"{uuid.uuid4()}.jpg"
                filepath = os.path.join("app/src/img/promo/", filename)
                with open(filepath, "wb") as f:
                    f.write(img_data)
                src_img = str(os.getenv("PATH_IMG")) + "promo/" + str(filename)
                update_data["src_img"] = src_img
            
            # Обновляем только если есть что обновлять
            if update_data:
                supabase.table("promocodes").update(update_data).eq("id", request.promocode_id).execute()
            
            return {
                "message": "Промокод успешно обновлен"
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка обновления: {str(e)}"
            )
    
    # Маршрут для получения акций (промокодов) админский
    @router.get("/fetch_promocodes_admin")
    async def fetch_promocodes_admin():
        try:
            promocodes_response = supabase.table("promocodes") \
                .select("*") \
                .order("created_at", desc=True) \
                .execute()
            promocodes = promocodes_response.data
            formatted_promocodes = []
            for promocode in promocodes:
                formatted_promocodes.append({
                    "promocode_id": promocode["id"],
                    "promocode": promocode["promocode"],
                    "description": promocode["description"],
                    "src_img": promocode["src_img"],
                    "is_acitve": promocode["is_active"],
                })
            
            return {
                "success": True,
                "promocodes": formatted_promocodes,
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при получении заказов: {str(e)}"
            )

    return router

    