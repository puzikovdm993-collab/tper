from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import boto3
import json
import os

app = Flask(__name__)
CORS(app)

# Конфигурация MinIO
MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
MINIO_BUCKET = os.getenv('MINIO_BUCKET', 'json-data')

# Инициализация клиента MinIO
minio_client = boto3.client(
    's3',
    endpoint_url=f'http://{MINIO_ENDPOINT}',
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    use_ssl=False
)

def ensure_bucket_exists():
    """Убедиться, что бакет существует"""
    try:
        minio_client.head_bucket(Bucket=MINIO_BUCKET)
        return True
    except Exception as e:
        # Если MinIO недоступен, просто игнорируем
        print(f"Warning: MinIO unavailable - {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data', methods=['GET'])
def get_data():
    """Получить данные из MinIO"""
    try:
        response = minio_client.get_object(Bucket=MINIO_BUCKET, Key='data.json')
        data = json.loads(response['Body'].read().decode('utf-8'))
        return jsonify(data)
    except Exception as e:
        # Если файл не существует или MinIO недоступен, возвращаем пустую структуру
        print(f"Info: Returning empty data - {e}")
        return jsonify({})

@app.route('/api/data', methods=['POST', 'PUT'])
def save_data():
    """Сохранить данные в MinIO"""
    try:
        data = request.get_json()
        if data is None:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Пытаемся сохранить в MinIO, но не блокируем если недоступен
        try:
            minio_client.put_object(
                Bucket=MINIO_BUCKET,
                Key='data.json',
                Body=json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8'),
                ContentType='application/json'
            )
        except Exception as e:
            print(f"Warning: Could not save to MinIO - {e}")
        
        return jsonify({'status': 'success', 'message': 'Data saved (MinIO may be unavailable)'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
