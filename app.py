from fastapi import FastAPI, Form, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any
from auth import router as auth_router

from db import get_db_connection
from transaction_service import check_balance, update_user, create_transaction, generate_sms
from utilities import parse_sms_message

# Initialize FastAPI app
app = FastAPI(title="Payment API", description="API for handling payments via SMS")
app.include_router(auth_router)

# Define request model for /sync endpoint
class SyncRequest(BaseModel):
    id: int

@app.post("/sync",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "User details retrieved successfully"},
        404: {"description": "User not found"},
        500: {"description": "Internal server error"}
    })
async def sync_user(request: SyncRequest) -> Dict[str, Any]:
    """Retrieve user information by ID"""

    conn = None
    cursor = None

    try:
        conn, cursor = get_db_connection()

        cursor.execute("SELECT id, name, balance FROM users WHERE id = %s;", (request.id,))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user_id, name, balance = user
        return {
            "id": user_id,
            "name": name,
            "balance": balance
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user details: {str(e)}"
        )

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.post("/sms-webhook",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Transaction processed successfully"},
        400: {"description": "Invalid SMS format or transaction data"},
        404: {"description": "User not found"},
        402: {"description": "Insufficient funds"},
        500: {"description": "Internal server error"}
    })
async def receive_sms(Body: str = Form(...)) -> Dict[str, Any]:
    """Process an SMS payment request"""

    try:
        # Parse the SMS message
        sms_data = parse_sms_message(Body)
        if not sms_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid SMS format"
            )

        # Convert string IDs to integers for database operations
        sender_id = int(sms_data.client_id)
        receiver_id = int(sms_data.receiver_id)
        amount = float(sms_data.amount)

        # Check balance
        has_sufficient_balance = check_balance(sender_id, amount)

        if not has_sufficient_balance:
            # Insufficient balance case
            create_transaction(sender_id, receiver_id, amount, "insufficient_balance")
            response_sms = generate_sms(sender_id, amount, "unsuccessful","sent")

            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "status": "error",
                    "message": response_sms,
                    "error_code": "INSUFFICIENT_FUNDS"
                }
            )

        # Update users' balances
        update_success = update_user(sender_id, receiver_id, amount)

        if not update_success:
            # Transaction failed during update
            create_transaction(sender_id, receiver_id, amount, "failed")
            response_sms = generate_sms(sender_id, amount, "failed","sent")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": response_sms,
                    "error_code": "TRANSACTION_FAILED"
                }
            )

        # Transaction successful
        create_transaction(sender_id, receiver_id, amount, "successful")
        response_sms = generate_sms(sender_id, amount, "successful","sent")
        response_sms = generate_sms(receiver_id, amount, "successful","recieved")

        return {
            "status": "success",
            "message": response_sms,
            "transaction_status": "COMPLETED"
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input data: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing transaction: {str(e)}"
        )

class AddBalanceRequest(BaseModel):
    user_id: int
    amount: int

@app.post("/addbalance",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Balance updated successfully"},
        404: {"description": "User not found"},
        500: {"description": "Internal server error"}
    })
def add_balance(request: AddBalanceRequest) -> Dict[str, Any]:
    conn = None
    cursor = None

    try:
        conn, cursor = get_db_connection()

        # Check if user exists
        cursor.execute("SELECT balance FROM users WHERE id = %s;", (request.user_id,))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        current_balance = user[0]
        new_balance = current_balance + request.amount

        # Update balance
        cursor.execute(
            "UPDATE users SET balance = %s WHERE id = %s;",
            (new_balance, request.user_id)
        )
        conn.commit()

        return {
            "status": "success",
            "user_id": request.user_id,
            "new_balance": new_balance
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update balance: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
