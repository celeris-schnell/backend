from typing import Optional
from dataclasses import dataclass

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