from flask import Flask, request, jsonify
import sqlite3
from twilio.rest import Client

app = Flask(__name__)

# Twilio setup
account_sid = 'YOUR_TWILIO_ACCOUNT_SID'
auth_token = 'YOUR_TWILIO_AUTH_TOKEN'
client = Client(account_sid, auth_token)

@app.route('/checkin', methods=['POST'])
def checkin_visitor():
    name = request.form['name']
    phone_number = request.form['phone_number']

    # Add the visitor to the database
    conn = sqlite3.connect('visitors.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO Visitors (name, phone_number, in_queue, check_in_time) VALUES (?, ?, 1, datetime("now"))', (name, phone_number))
    conn.commit()
    conn.close()

    # Notify the visitor of their position in the queue
    queue_position = get_queue_position(phone_number)
    message = f"Hello {name}, you're number {queue_position} in the queue. We'll notify you when it's your turn."
    client.messages.create(body=message, from_='YOUR_TWILIO_PHONE_NUMBER', to=phone_number)

    return jsonify(status='checked in', queue_position=queue_position)

@app.route('/notify_next', methods=['GET'])
def notify_next():
    conn = sqlite3.connect('visitors.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, phone_number FROM Visitors WHERE in_queue=1 ORDER BY check_in_time ASC LIMIT 1')
    visitor = cursor.fetchone()
    conn.close()

    if visitor:
        name, phone_number = visitor
        message = f"Hello {name}, it's your turn now!"
        client.messages.create(body=message, from_='YOUR_TWILIO_PHONE_NUMBER', to=phone_number)
        return jsonify(status='notified', name=name)
    else:
        return jsonify(status='no visitors in queue')

def get_queue_position(phone_number):
    conn = sqlite3.connect('visitors.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM Visitors WHERE in_queue=1 AND check_in_time < (SELECT check_in_time FROM Visitors WHERE phone_number=?)', (phone_number,))
    position = cursor.fetchone()[0] + 1
    conn.close()
    return position

if __name__ == "__main__":
    app.run(debug=True)
