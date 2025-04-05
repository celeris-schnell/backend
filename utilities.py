from fastapi import HTTPException
from typing import Optional
from dataclasses import dataclass

from db import get_db_connection

@dataclass
class SMSData:
    client_id: str
    receiver_id: str
    amount: float

def parse_sms_message(message: str) -> Optional[SMSData]:
    """
    Parse an SMS message in the format 'client id | receiver id | amount'

    Args:
        message: The SMS message text to parse

    Returns:
        SMSData object or None if parsing fails
    """
    try:
        # Split the message by the delimiter and remove any whitespace
        parts = [part.strip() for part in message.split("|")]

        # Verify we have exactly 3 parts
        if len(parts) != 3:
            return None

        client_id, receiver_id, amount_str = parts

        # Convert amount to float and validate
        amount = float(amount_str)
        if amount <= 0:
            return None

        # Validate IDs are not empty
        if not client_id or not receiver_id:
            return None

        return SMSData(
            client_id=client_id,
            receiver_id=receiver_id,
            amount=amount
        )

    except Exception as e:
        print(f"Error parsing SMS message: {str(e)}")
        return None

def create_user(id: int, balance: int, name: str, phoneNumber: str):
    conn = None
    cursor = None

    try:
        conn, cursor = get_db_connection()

        cursor.execute("""
            INSERT INTO users (id, balance, name, "phoneNumber")
            VALUES (%s, %s, %s, %s)
        """, (id, balance, name, phoneNumber))

        conn.commit()

    except Exception as e:
        print(f"Error during signup: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
