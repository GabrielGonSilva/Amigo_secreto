import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from app import app, db


def setup_database():
    print("🔄 Configurando banco de dados...")

    try:
        with app.app_context():
            db.create_all()
            print("✅ Tabelas criadas com sucesso!")

            if os.environ.get('FLASK_ENV') == 'development':
                print("🔄 Adicionando dados de exemplo...")
                print("✅ Dados de exemplo adicionados!")

    except Exception as e:
        print(f"❌ Erro ao configurar banco: {e}")
        sys.exit(1)


if __name__ == '__main__':
    setup_database()