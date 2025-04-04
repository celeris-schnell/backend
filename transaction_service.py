from db import get_db_connection

def check_balance(client_id: int, amount: float) -> bool:
    """
    Check if a user has sufficient balance for a transaction

    Args:
        client_id: The ID of the user making the payment
        amount: The transaction amount

    Returns:
        bool: True if sufficient balance, False otherwise
    """
    conn = None
    cursor = None

    try:
        conn, cursor = get_db_connection()

        cursor.execute("SELECT balance FROM users WHERE id = %s;", (client_id,))
        result = cursor.fetchone()

        if not result:
            return False

        balance = result[0]
        return balance >= amount

    except Exception as e:
        print(f"Error checking balance: {e}")
        return False

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def generate_sms(amount: float, status: str) -> str:
    """Generate SMS response message based on transaction status."""
    return f"{amount}|{status}"

def create_transaction(sender_id: int, receiver_id: int, amount: float, status: str) -> bool:
    """
    Record a transaction in the database

    Args:
        sender_id: The ID of the sender
        receiver_id: The ID of the receiver
        amount: Transaction amount
        status: Transaction status

    Returns:
        bool: True if transaction was recorded successfully
    """
    conn = None
    cursor = None

    try:
        conn, cursor = get_db_connection()

        cursor.execute("""
            INSERT INTO transactions (sender_id, receiver_id, amount, status)
            VALUES (%s, %s, %s, %s);
        """, (sender_id, receiver_id, amount, status))

        conn.commit()
        return True

    except Exception as e:
        print(f"Error recording transaction: {e}")
        return False

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def update_user(sender_id: int, receiver_id: int, amount: float) -> bool:
    """
    Update the balances of both sender and receiver

    Args:
        sender_id: The ID of the sender
        receiver_id: The ID of the receiver
        amount: Transaction amount

    Returns:
        bool: True if both balances were updated successfully
    """
    conn = None
    cursor = None

    try:
        conn, cursor = get_db_connection()

        # Start transaction
        cursor.execute("BEGIN")

        # Update sender's balance (decrease)
        cursor.execute("""
            UPDATE users
            SET balance = balance - %s
            WHERE id = %s
            RETURNING id;
        """, (amount, sender_id))
        sender_update = cursor.fetchone()

        # Update receiver's balance (increase)
        cursor.execute("""
            UPDATE users
            SET balance = balance + %s
            WHERE id = %s
            RETURNING id;
        """, (amount, receiver_id))
        receiver_update = cursor.fetchone()

        # Check if both updates were successful
        if sender_update and receiver_update:
            conn.commit()
            return True
        else:
            conn.rollback()
            return False

    except Exception as e:
        print(f"Error updating balances: {e}")
        if conn:
            conn.rollback()
        return False

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()