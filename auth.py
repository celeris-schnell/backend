from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from db import get_db_connection
from utilities import create_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    phoneNumber: str

@router.post("/signup")
def signup(payload: SignupRequest):
    conn = None
    cursor = None

    try:
        conn, cursor = get_db_connection()

        cursor.execute("SELECT id FROM auth_table WHERE email = %s;", (payload.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")

        cursor.execute("""
            INSERT INTO auth_table (email, password, name, "phoneNumber")
            VALUES (%s, %s, %s, %s)
            RETURNING id;
        """, (payload.email, payload.password, payload.name, payload.phoneNumber))

        user_id = cursor.fetchone()[0]
        conn.commit()

        create_user(user_id, 0, payload.name, payload.phoneNumber)

        return {"message": "Signup successful", "user_id": user_id}

    except Exception as e:
        print(f"Error during signup: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/login")
def login(payload: LoginRequest):
    conn = None
    cursor = None

    try:
        conn, cursor = get_db_connection()

        cursor.execute("""
            SELECT id, password FROM auth_table WHERE email = %s;
        """, (payload.email,))
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Email not found")

        user_id, stored_password = result

        if stored_password != payload.password:
            raise HTTPException(status_code=401, detail="Incorrect password")

        return {"message": "Login successful", "user_id": user_id}

    except Exception as e:
        print(f"Error during login: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
