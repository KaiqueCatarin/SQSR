from flask import Flask, render_template, request
import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables from a .env file
load_dotenv()

# Database connection parameters
server = '35.198.20.9'  # Your GCP SQL Server public IP
port = 1433             # Default SQL Server port
database = 'RiotDB'     # Your database name
username = 'sqlserver'  # Your SQL Server username
password = os.getenv('DB_PASSWORD')  # Retrieve password from environment variable

# Check if the password was loaded
if not password:
    raise ValueError("Database password not found. Please set the DB_PASSWORD environment variable.")

# Construct the database connection string
connection_url = (
    f"mssql+pyodbc://{username}:{password}@{server}:{port}/{database}"
    "?driver=ODBC+Driver+18+for+SQL+Server"
    "&Encrypt=yes"
    "&TrustServerCertificate=yes"
)

# Create the SQLAlchemy engine
engine = create_engine(connection_url)

# Function to retrieve the 3 most played champions
def get_most_played_champions(summoner_name):
    query = f"""
    SELECT TOP 3 championName, COUNT(*) AS games_played
    FROM Detalhes_Liga_Invocador
    WHERE riotIdGameName = '{summoner_name}'
    GROUP BY championName
    ORDER BY games_played DESC
    """
    # Fetch data from the database
    df_champions = pd.read_sql_query(query, engine)
    return df_champions

# Function to calculate KDA, win rate, CS/min, and games played for the top 3 played champions
def calculate_champion_stats(summoner_name, champions):
    stats = []
    
    for champion in champions['championName']:
        query = f"""
        SELECT 
            SUM(kills) AS total_kills,
            SUM(deaths) AS total_deaths,
            SUM(assists) AS total_assists,
            COUNT(CASE WHEN win = 1 THEN 1 END) AS wins,
            COUNT(*) AS total_games,
            SUM(totalMinionsKilled) AS total_cs,
            SUM(timePlayed) AS total_time_played
        FROM Detalhes_Liga_Invocador
        WHERE riotIdGameName = '{summoner_name}' AND championName = '{champion}'
        """
        # Fetch data for each champion
        df_stats = pd.read_sql_query(query, engine)
        
        # Calculate KDA
        kills = df_stats['total_kills'].iloc[0]
        deaths = df_stats['total_deaths'].iloc[0]
        assists = df_stats['total_assists'].iloc[0]
        kda = (kills + assists) / (deaths if deaths > 0 else 1)
        
        # Calculate win rate
        total_games = df_stats['total_games'].iloc[0]
        wins = df_stats['wins'].iloc[0]
        win_rate = (wins / total_games) * 100 if total_games > 0 else 0
        
        # Calculate CS/min
        total_cs = df_stats['total_cs'].iloc[0]
        total_time_played = df_stats['total_time_played'].iloc[0]
        cs_per_min = total_cs / (total_time_played / 60) if total_time_played > 0 else 0
        
        # Append stats to the list
        stats.append({
            'Champion': champion,
            'Games Played': total_games,
            'KDA': round(kda, 2),
            'Win Rate (%)': round(win_rate, 2),
            'CS/Min': round(cs_per_min, 2)
        })
    
    return pd.DataFrame(stats)

# Flask route to display the form and handle user input
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        summoner_name = request.form.get('summoner_name')
        
        # Retrieve the 3 most played champions
        df_most_played_champions = get_most_played_champions(summoner_name)
        
        # Calculate KDA, Winrate, CS/min, and games played for the top 3 champions
        champion_stats = calculate_champion_stats(summoner_name, df_most_played_champions)
        
        # Convert the DataFrame to HTML for display
        stats_html = champion_stats.to_html(index=False)
        
        return render_template('index.html', summoner_name=summoner_name, stats_html=stats_html)
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
