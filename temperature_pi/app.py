from flask import Flask, request, render_template, redirect, url_for
import sqlite3
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import os

app = Flask(__name__, template_folder='templates/')

def init_sqlite_db():
    conn = sqlite3.connect('sensor_data.db')
    print("Opened database successfully")
    
    conn.execute('''
    CREATE TABLE IF NOT EXISTS readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        temperature REAL,
        humidity REAL,
        timestamp DATETIME DEFAULT (datetime(CURRENT_TIMESTAMP, '+3 hours'))
    )
    ''')
    print("Table created successfully")
    conn.close()

@app.route('/add', methods=['POST', 'GET'])
def add_reading():
    if request.method == 'POST':
        try:
            temperature = request.form['temperature']
            humidity = request.form['humidity']
            
            with sqlite3.connect('sensor_data.db') as con:
                cur = con.cursor()
                cur.execute("INSERT INTO readings (temperature, humidity) VALUES (?, ?)", (temperature, humidity))
                con.commit()
                msg = "Reading successfully added"
                print("Added", temperature, ' + ', humidity) 
        except:
            con.rollback()
            msg = "Error in insert operation"
        finally:
            return redirect(url_for('home'))
        con.close()

@app.route('/')
def home():
    conn = sqlite3.connect('sensor_data.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM readings ORDER BY timestamp DESC")
    rows = cur.fetchall()

    cur.execute("SELECT temperature FROM readings ORDER BY timestamp DESC LIMIT 1")
    current_temperature = cur.fetchone()['temperature']
    #current_temperature = 0
    
    today = datetime.now().date()
    cur.execute("SELECT temperature FROM readings WHERE DATE(timestamp) = ?", (today,))
    today_readings = [row['temperature'] for row in cur.fetchall()]
    average_temperature = sum(today_readings) / len(today_readings) if today_readings else 0
    min_temperature = min(today_readings) if today_readings else 0
    max_temperature = max(today_readings) if today_readings else 0
    
    one_week_ago = datetime.now() - timedelta(days=7)
    cur.execute("SELECT MIN(temperature) as min_temp FROM readings WHERE timestamp >= ?", (one_week_ago,))
    min_temp_past_week = cur.fetchone()['min_temp']
    
    cur.execute("SELECT MAX(temperature) as max_temp FROM readings WHERE timestamp >= ?", (one_week_ago,))
    max_temp_past_week = cur.fetchone()['max_temp']
    
    cur.execute("SELECT timestamp, temperature FROM readings WHERE timestamp >= ?", (one_week_ago,))
    rows_for_plot = cur.fetchall()
    
    conn.close()
    
    timestamps = [datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S') for row in rows_for_plot]
    temperatures = [row['temperature'] for row in rows_for_plot]
    
    week_number = datetime.now().isocalendar()[1]
    
    plt.figure(figsize=(10, 5))
    plt.plot(timestamps, temperatures, marker='o', linestyle='-', color='b')
    plt.xlabel('Timestamp')
    plt.ylabel('Temperature (°C)')
    plt.title('Temperature Evolution Over the Past Week (' + str(week_number) + ')')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    if not os.path.exists('static/weekly_plots'):
        os.makedirs('static/weekly_plots')
    
    plot_filename = f'weekly_plots/temperature_evolution_week_{week_number}.png'
    plt.savefig('static/' + plot_filename)
    
    return render_template('list.html', rows=rows, current_temperature=current_temperature,
                           average_temperature=average_temperature, min_temperature=min_temperature,
                           max_temperature=max_temperature, min_temp_past_week=min_temp_past_week,
                           max_temp_past_week=max_temp_past_week, plot_filename=plot_filename, week_number=week_number)

if __name__ == '__main__':
    init_sqlite_db()
    app.run(host='169.254.35.2', port=5000, debug=True)
