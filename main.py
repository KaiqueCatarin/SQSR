from flask import Flask, render_template, request
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import urllib.parse

app = Flask(__name__)

# Database connection parameters
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '1433')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

# Check if all required environment variables are set
if not all([DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD]):
    missing_vars = [var for var in ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD'] if not os.getenv(var)]
    raise ValueError(f"Please set all required environment variables: {', '.join(missing_vars)}.")

# URL-encode the password if it contains special characters
DB_PASSWORD_ENCODED = urllib.parse.quote_plus(DB_PASSWORD)

# Construct the database URL for SQL Server
DATABASE_URL = (
    f"mssql+pyodbc://{DB_USER}:{DB_PASSWORD_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    "?driver=ODBC+Driver+18+for+SQL+Server"
    "&Encrypt=yes"
    "&TrustServerCertificate=yes"
)

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a configured "Session" class
Session = sessionmaker(bind=engine)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    riot_id_game_name = request.form['riotIdGameName']
    try:
        # Create a new session
        session = Session()

        # Use parameterized query to prevent SQL injection
        query = text("SELECT * FROM Detalhes_Liga_Invocador WHERE riotIdGameName = :name")
        result = session.execute(query, {'name': riot_id_game_name})
        rows = result.mappings().all()

        session.close()

        if not rows:
            error_message = f'No results found for "{riot_id_game_name}".'
            return render_template('index.html', error=error_message)
        else:
            # Since rows are already mappings (dictionaries), you can use them directly
            data = [dict(row) for row in rows]  # Or simply data = rows
            return render_template('results.html', data=data, riotIdGameName=riot_id_game_name)
    except Exception as e:
        # Log the exception
        print(f"An error occurred: {e}")
        error_message = "An error occurred while processing your request."
        return render_template('index.html', error=error_message)


if __name__ == '__main__':
    app.run(debug=True)
