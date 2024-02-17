from flask import Flask, render_template
from control_panel import ControlPanel

app = Flask(__name__)
control_panel: ControlPanel = None

@app.route('/button_pressed', methods=['GET'])
def button_pressed():
    control_panel.button_is_pressed = True
    control_panel.button_press_acknowledged = False
    return "Button press acknowledged", 200


@app.route('/button_unpressed', methods=['GET'])
def button_unpressed():
    control_panel.button_is_pressed = False
    return "Button unpress acknowledged", 200


@app.route('/status.html')
def status():
    return render_template('status.html', users=control_panel.account_manager.users)


def run_flask_app():
    app.run(host='0.0.0.0', port=5000, threaded=True)


if __name__ == "__main__":
    import threading
    control_panel = ControlPanel(run_window_manager=False)
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.start()
    while True:
        pass
    