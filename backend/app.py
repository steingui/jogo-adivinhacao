import os
import random
import time
from datetime import datetime
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Database configuration with environment variables
db_user = os.environ.get('POSTGRES_USER', 'postgres')
db_password = os.environ.get('POSTGRES_PASSWORD', 'postgres')
db_host = os.environ.get('POSTGRES_HOST', 'db')
db_port = os.environ.get('POSTGRES_PORT', '5432')
db_name = os.environ.get('POSTGRES_DB', 'guessing_game')

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Model
class Game(db.Model):
    __tablename__ = 'games'
    id = db.Column(db.Integer, primary_key=True)
    secret_number = db.Column(db.Integer, nullable=False)
    attempts = db.Column(db.Integer, default=0, nullable=False)
    status = db.Column(db.String(20), default='active', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'secret_number': self.secret_number if self.status == 'completed' else None,
            'attempts': self.attempts,
            'status': self.status,
            'created_at': self.created_at.isoformat() + 'Z',
            'completed_at': self.completed_at.isoformat() + 'Z' if self.completed_at else None
        }

# Initialize Database with simple connection retry logic
def init_db():
    retries = 5
    while retries > 0:
        try:
            with app.app_context():
                db.create_all()
                print("Conexão estabelecida e tabelas do banco de dados criadas com sucesso!")
                return
        except Exception as e:
            print(f"Banco de dados ainda não disponível. Retentando em 3 segundos... (Erro: {e})")
            retries -= 1
            time.sleep(3)
    print("Aviso: Não foi possível conectar ao banco de dados durante a inicialização.")

init_db()

@app.route('/api/game/start', methods=['POST'])
def start_game():
    try:
        secret = random.randint(1, 100)
        game = Game(secret_number=secret, attempts=0, status='active')
        db.session.add(game)
        db.session.commit()
        return jsonify({'game_id': game.id, 'message': 'Jogo iniciado com sucesso!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Falha ao iniciar jogo: {str(e)}'}), 500

@app.route('/api/game/guess', methods=['POST'])
def make_guess():
    data = request.get_json()
    if not data or 'game_id' not in data or 'guess' not in data:
        return jsonify({'error': 'Parâmetros inválidos. Informe game_id e guess.'}), 400
    
    try:
        game_id = data['game_id']
        guess = int(data['guess'])
        
        # Use session.get() in SQLAlchemy 2.0+ / Flask-SQLAlchemy 3.0+
        game = db.session.get(Game, game_id)
        if not game:
            return jsonify({'error': 'Jogo não encontrado.'}), 404
        
        if game.status == 'completed':
            return jsonify({'error': 'Este jogo já foi finalizado.'}), 400
            
        game.attempts += 1
        
        if guess == game.secret_number:
            game.status = 'completed'
            game.completed_at = datetime.utcnow()
            db.session.commit()
            return jsonify({
                'message': 'correct',
                'attempts': game.attempts,
                'status': game.status
            })
        elif guess > game.secret_number:
            db.session.commit()
            return jsonify({
                'message': 'too high',
                'attempts': game.attempts,
                'status': game.status
            })
        else:
            db.session.commit()
            return jsonify({
                'message': 'too low',
                'attempts': game.attempts,
                'status': game.status
            })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao processar palpite: {str(e)}'}), 500

@app.route('/api/game/history', methods=['GET'])
def get_history():
    try:
        games = Game.query.order_by(Game.created_at.desc()).limit(15).all()
        return jsonify([game.to_dict() for game in games])
    except Exception as e:
        return jsonify({'error': f'Falha ao buscar histórico: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({
            'status': 'healthy', 
            'database': 'connected',
            'container_id': os.environ.get('HOSTNAME', 'unknown') # useful for demonstrating load balancing
        }), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'database': 'error', 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
