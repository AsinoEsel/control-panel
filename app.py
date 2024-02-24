from flask import Flask, render_template, request, jsonify
from control_panel import ControlPanel
from esp_requests import ESPs

app = Flask(__name__)
control_panel: ControlPanel = None

@app.route('/button_pressed', methods=['GET'])
def button_pressed():
    control_panel.button_is_pressed = True
    control_panel.button_press_acknowledged = False
    return jsonify({"message": "Button press acknowledged"}, 200)


@app.route('/button_unpressed', methods=['GET'])
def button_unpressed():
    control_panel.button_is_pressed = False
    return jsonify({"message": "Button unpress acknowledged"}, 200)


@app.route('/api')
def handle_api():
    uid=request.args.get('uid')
    if uid:
        if not (esp := ESPs.get(request.remote_addr)):
            print(error := f"No known ESP with IP {request.remote_addr} exists.")
            return jsonify({"error": error}), 400
        if not (user := control_panel.account_manager.get_user_from_uid(uid)):
            print(error := f"No known user with UID {uid} exists.")
            return jsonify({"error": error, "uid": uid}), 200
        esp.checked_in_users.append(user)
        user.checkins[esp.level_name] = True
        print(message := f"User '{user.username}' with UID '{user.uid}' has checked into ESP '{esp.IP}' @ '{esp.level_name}'")
        return jsonify({"message": message, "uid": user.uid, "username": user.username}), 200
    else:
        return jsonify({"error": "UID not provided."}), 400


@app.route('/status')
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
    