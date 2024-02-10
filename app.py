from flask import Flask

app = Flask(__name__)
game_manager = None

@app.route('/button_pressed', methods=['GET'])
def button_pressed():
    game_manager.button_is_pressed = True
    game_manager.button_press_acknowledged = False
    return "Button press acknowledged", 200


@app.route('/button_unpressed', methods=['GET'])
def button_unpressed():
    game_manager.button_is_pressed = False
    return "Button unpress acknowledged", 200


def run_flask_app():
    app.run(host='0.0.0.0', port=5000, threaded=True)