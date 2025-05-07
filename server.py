import json
from datetime import datetime
import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import io
import base64
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    html = f'''
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>تسجيل المصروفات اليومية</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                background-color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            input {{
                width: 100%;
                padding: 8px;
                margin: 8px 0;
                border: 1px solid #ddd;
                border-radius: 4px;
            }}
            button {{
                width: 100%;
                padding: 10px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }}
            button:hover {{
                background-color: #45a049;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>تسجيل المصروفات اليومية</h1>
            <form id="expenseForm" onsubmit="handleSubmit(event)">
                <input type="date" id="date" name="date" value="{current_date}">
                <input type="text" id="description" name="description" placeholder="بيان المصروف" required autofocus>
                <input type="number" id="amount" name="amount" placeholder="القيمة" step="0.01" required>
                <button type="submit">إضافة المصروف</button>
            </form>
        </div>
        <script>
            function handleSubmit(event) {{
                event.preventDefault();
                const formData = new FormData(event.target);
                fetch('/submit', {{
                    method: 'POST',
                    body: JSON.stringify(Object.fromEntries(formData)),
                    headers: {{
                        'Content-Type': 'application/json'
                    }}
                }}).then(() => {{
                    event.target.reset();
                    document.getElementById('description').focus();
                }});
            }}
        </script>
    </body>
    </html>
    '''
    return html

@app.route('/submit', methods=['POST'])
def submit():
    try:
        # Load credentials from environment variable
        creds_json = os.environ.get('GOOGLE_CREDENTIALS')
        if not creds_json:
            raise ValueError('GOOGLE_CREDENTIALS environment variable is not set')
        
        # Decode the base64 credentials
        creds_bytes = base64.b64decode(creds_json)
        creds_info = json.loads(creds_bytes)
        
        # Create credentials
        creds = Credentials.from_service_account_info(
            creds_info,
            scopes=['https://www.googleapis.com/auth/spreadsheets'])
        
        # Build the service
        service = build('sheets', 'v4', credentials=creds)
        
        # The ID of the spreadsheet
        spreadsheet_id = '1HsmoQaLpyHDAwAHz6QaR-TieVCWUK54g0f3fF-rY0PQ'
        
        # Prepare the data to be written
        values = [
            [request.json['date'], request.json['description'], float(request.json['amount'])]
        ]
        
        # Prepare the request
        body = {
            'values': values
        }
        
        # Append the data to the sheet
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range='Sheet1!A1:C1',
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        
        return jsonify({'status': 'success', 'message': f'Successfully added {result.get("updates").get("updatedCells")} cells'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
