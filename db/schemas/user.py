def user_schema(user) -> dict:
    return {"id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"],
            "password": user["password"]}

def users_schema(users) -> list:
    return [user_schema(user) for user in users]

def basic_function():
    pass

def usuario_schema(user) -> dict:
    return {"id": str(user["_id"]),
            "username":user["username"],
            "sentadilla": user["sentadilla"],
            "peso_muerto": user["peso_muerto"],
            "press_banca": user["press_banca"]}