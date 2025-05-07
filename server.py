from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import json
from datetime import datetime
import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import pickle

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
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
            self.wfile.write(html.encode('utf-8'))

    def do_POST(self):
        if self.path == '/submit':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Save to Google Sheets
            try:
                # Load credentials
                creds = None
                if os.path.exists('token.pickle'):
                    with open('token.pickle', 'rb') as token:
                        creds = pickle.load(token)
                
                if not creds:
                    # Load credentials
                    creds = Credentials.from_service_account_file(
                        'credentials.json',
                        scopes=['https://www.googleapis.com/auth/spreadsheets'])
                    
                    # Save credentials for future use
                    with open('token.pickle', 'wb') as token:
                        pickle.dump(creds, token)
                
                # Build the service
                service = build('sheets', 'v4', credentials=creds)
                
                # The ID of the spreadsheet
                spreadsheet_id = '1HsmoQaLpyHDAwAHz6QaR-TieVCWUK54g0f3fF-rY0PQ'
                
                # Prepare the data to be written
                values = [
                    [data['date'], data['description'], float(data['amount'])]
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
                
                print(f"Successfully added {result.get('updates').get('updatedCells')} cells")
            except Exception as e:
                print(f"Error saving to Google Sheets: {str(e)}")
            
            self.send_response(200)
            self.end_headers()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    run()
