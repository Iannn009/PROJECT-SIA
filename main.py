from flask import Flask, render_template, jsonify, request
import serial
import threading

app = Flask(__name__)

sensor_data = {
    'distance': 0.0,
    'duration': 0,
    'led1_status': 'OFF',
    'led2_status': 'OFF',
    'buzzer_status': 'OFF'
}

SERIAL_PORT = 'COM5'
BAUD_RATE = 9600

ser = None

def connect_serial():
    global ser
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {SERIAL_PORT}")
    except:
        print(f"Could not connect to {SERIAL_PORT}")

def send_to_arduino(command):
    if ser and ser.is_open:
        try:
            ser.write((command + '\n').encode())
            print(f"Sent to Arduino: {command}")
        except:
            print("Error sending command")

def read_serial():
    connect_serial()
    while True:
        if ser and ser.in_waiting > 0:
            try:
                line = ser.readline().decode('utf-8').strip()
                print(f"Arduino: {line}")
                
                if 'Distance:' in line and 'CM' in line:
                    try:
                        parts = line.split('|')
                        if len(parts) >= 1:
                            d = parts[0].split(':')[1].split('CM')[0].strip()
                            sensor_data['distance'] = float(d)
                    except:
                        pass
                
                if 'IN RANGE' in line:
                    sensor_data['buzzer_status'] = 'ON'
                    sensor_data['led2_status'] = 'ON'
                    sensor_data['led1_status'] = 'OFF'
                    
                elif 'OUT OF RANGE' in line:
                    sensor_data['buzzer_status'] = 'OFF'
                    sensor_data['led1_status'] = 'ON'
                    sensor_data['led2_status'] = 'OFF'
                    
            except:
                pass

threading.Thread(target=read_serial, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    return jsonify(sensor_data)

@app.route('/api/command', methods=['POST'])
def post_command():
    data = request.get_json()
    cmd = data.get('command')
    val = data.get('value')
    
    if cmd == 'led1':
        sensor_data['led1_status'] = val.upper()
        send_to_arduino(f"LED1_{val.upper()}")
        
    elif cmd == 'led2':
        sensor_data['led2_status'] = val.upper()
        send_to_arduino(f"LED2_{val.upper()}")
        
    elif cmd == 'buzzer':
        sensor_data['buzzer_status'] = val.upper()
        send_to_arduino(f"BUZZER_{val.upper()}")
    
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)