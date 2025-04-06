# Quick Start

1. Create a virtual environment

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

2. Install Dependencies

   ```bash
   pip install -r requirements.txt
   ```

3. Run with Uvicorn

   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

4. Expose with Ngrok

   ```bash
   ngrok http 8000
   ```

5. Test the SMS Webhook

   You can test the webhook by sending a POST request to the `/sms-webhook/` endpoint with a form field named `Body`.

   ```bash
   curl -X POST http://localhost:8000/sms-webhook/ -d "Body=Hello"
   ```

## Description

This is the backend for a self-hosted SMS server (kind of like our own Twilio) which will connect and make all database actions on Supabase later on.

## The .env file

user=<from supabase>
password=<from supabase>
host=<from supabase>
port=<from supabase>
dbname=<from supabase>
ip=<phone-ip-address-with-port>

## Example Code

```python
from fastapi import FastAPI, Form

app = FastAPI()

@app.post("/sms-webhook/")
async def receive_sms(Body: str = Form(...)):
    print(f"Received SMS: {Body}")
    return {"status": "SMS received"}
```
