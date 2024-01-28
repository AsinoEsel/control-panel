from flask import Flask

app = Flask(__name__)

@app.route('/button_pressed', methods=['GET'])
def button_pressed():
    print("Button was pressed!")
    # You can add any action you want to perform here.
    return "Button press acknowledged", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)