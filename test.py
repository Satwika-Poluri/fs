from flask import Flask, render_template
import mysql.connector  # Use the appropriate MySQL library

app = Flask(__name__)

# Database configuration
db_config = {
    "host": "Satwika",
    "user": "system",
    "password": "root",
    "database": "spm",
}

# Attempt to establish a database connection
try:
    # Create a database connection
    db_connection = mysql.connector.connect(**db_config)

    # Check if the connection was successful
    if db_connection.is_connected():
        print("Database connection established successfully!")

except mysql.connector.Error as e:
    # Handle the error if the connection fails
    print(f"Error connecting to the database: {e}")

# Close the database connection when you're done
if 'db_connection' in locals():
    db_connection.close()

@app.route('/home')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)
