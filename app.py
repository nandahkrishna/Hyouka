# Authors: Nanda H Krishna (https://github.com/nandahkrishna), Abhijith Ragav (https://github.com/abhijithragav)

import os
import json
import threading
import subprocess
import hmac
from hashlib import sha1
from flask import Flask, jsonify, redirect, request, abort
import numpy as np
import pyrebase
import slack

app = Flask(__name__)
app.debug = True

tars_admin = os.environ.get("TARS_ADMIN")
tars_token = os.environ.get("TARS_TOKEN")
tars = slack.WebClient(token=tars_token)

github_token = os.environ.get("GITHUB_TOKEN")
github_secret = os.environ.get("GITHUB_SECRET")

hyouka_firebase_config = {
  "apiKey": os.environ.get("FIREBASE_API_KEY"),
  "authDomain": os.environ.get("HYOUKA_FB_AD"),
  "databaseURL": os.environ.get("HYOUKA_FB_URL"),
  "storageBucket": os.environ.get("HYOUKA_FB_SB")
}
firebase = pyrebase.initialize_app(hyouka_firebase_config)
key_fb_hyouka = os.environ.get("KEY_FB_HYOUKA")

tars_firebase_config = {
  "apiKey": os.environ.get("TARS_FIREBASE_KEY"),
  "authDomain": os.environ.get("TARS_FB_AD"),
  "databaseURL": os.environ.get("TARS_FB_URL"),
  "storageBucket": os.environ.get("TARS_FB_SB")
}
tars_firebase = pyrebase.initialize_app(tars_firebase_config)
key_fb_tars = os.environ.get("KEY_FB_TARS")

@app.route("/", methods=["GET"])
def index():
    return redirect("https://solarillionfoundation.org/projects/Hyouka")

@app.route("/python", methods=["POST"])
def python():
    header_signature = request.headers.get("X-Hub-Signature")
    if header_signature is None:
        abort(403)
    sha_type, signature = header_signature.split("=")
    if sha_type != "sha1":
        abort(501)
    mac = hmac.new(bytes(github_secret, "utf-8"), msg=request.data, digestmod="sha1")
    if not hmac.compare_digest(str(mac.hexdigest()), signature):
        abort(403)
    payload = request.get_json()
    message = payload["head_commit"]["message"]
    if "Delete" in message:
        db = firebase.database()
        github = payload["repository"]["owner"]["login"]
        slack_id = db.child(key_fb_hyouka).child(github).child("slack").get().val()
        chat = tars.im_open(user=slack_id).data["channel"]["id"]
        tars.chat_postMessage(channel=chat, text="You deleted " + message.split()[1])
        return "OK", 200
    thread = threading.Thread(target=python_tester, args=(payload,))
    thread.start()
    return "OK", 200

def python_tester(payload):
    db = firebase.database()
    data = db.child(key_fb_hyouka).get().val()
    repo = payload["repository"]["full_name"]
    id = payload["repository"]["owner"]["login"]
    name = data[id]["name"]
    status = data[id]["progress"]
    group = data[id]["group"]
    slack_id = data[id]["slack"]
    chat = tars.im_open(user=slack_id).data["channel"]["id"]
    if status == "py1":
        functions = {
            0: "number_pattern",
            1: "zero_star_pattern",
            2: "trigonometric_pattern",
            3: "dictionary_lookup",
            4: "round_off",
            5: "perfect_squares"
        }
        try:
            os.system("curl -H 'Authorization: token " + github_token + "' -H 'Accept: application/vnd.github.v3.raw' -O -L https://api.github.com/repos/" + repo + "/contents/Module1.ipynb")
        except:
            return
        s = subprocess.run(["python", "Py1Test.py"], capture_output=True)
        s = str(s.stdout.decode("utf-8")).split("\n")[-2]
        eval = json.loads(s)
        if sum(eval) == 6:
            tars.chat_postMessage(channel=chat, text="Congrats! You have completed Module 1. You can now move on to Module 2. Impressive!")
            db.child(key_fb_hyouka).child(id).update({"progress": "py2"})
            message = name + " has completed Py1."
            tars.chat_postMessage(channel=tars_admin, text=message)
            tars_db = tars_firebase.database()
            tars_db.child(key_fb_tars).child("orientee").child(slack_id).update({"progress": "py2"})
        else:
            check = np.where(np.array(eval) == 0)[0]
            if len(check) != 6:
                if 1 in eval:
                    tars.chat_postMessage(channel=chat, text="You did these right:")
                    for i in range(len(eval)):
                        if eval[i] == 1:
                            tars.chat_postMessage(channel=chat, text=functions[i])
            if len(check) > 0:
                if 0 in eval:
                    tars.chat_postMessage(channel=chat, text="Oops! Please check these functions and try submitting again:")
                    for value in check:
                        tars.chat_postMessage(channel=chat, text=functions[value])
            tars.chat_postMessage(channel=chat, text="Do contact a TA if you have any doubts!")
        os.system("rm -rf Module*")
    elif status == "py2":
        functions = {
            0: "pickle_to_csv",
            1: "count_unique",
            2: "add_binary",
            3: "compute_resp",
            4: "plot_raw",
            5: "plot_coloured",
            6: "random_numbers"
        }
        try:
            os.system("curl -H 'Authorization: token " + github_token + "' -H 'Accept: application/vnd.github.v3.raw' -O -L https://api.github.com/repos/" + repo + "/contents/Module2.ipynb")
        except:
            return
        s = subprocess.run(["python", "Py1Test.py"], capture_output=True)
        s = str(s.stdout.decode("utf-8")).split("\n")[-2]
        eval = json.loads(s)
        if sum(eval) == 7:
            db.child(key_fb_hyouka).child(id).update({"progress": "py2v"})
            tars.chat_postMessage(channel=chat, text="You have almost completed Module 2. Get your plots verified by a TA, and then move on to Module 3. Great job!")
            message = name + " has completed Py2, verify and update progress with TARS."
            tars.chat_postMessage(channel=tars_admin, text=message)
        else:
            check = np.where(np.array(eval) == 0)[0]
            if len(check) != 7:
                if 1 in eval:
                    tars.chat_postMessage(channel=chat, text="You did these right:")
                    for i in range(len(eval)):
                        if eval[i] == 1:
                            tars.chat_postMessage(channel=chat, text=functions[i])
            if len(check) > 0:
                if 0 in eval:
                    tars.chat_postMessage(channel=chat, text="Oops! Please check these functions and try submitting again:")
                    for value in check:
                        tars.chat_postMessage(channel=chat, text=functions[value])
            tars.chat_postMessage(channel=chat, text="Do contact a TA if you have any doubts!")
        os.system("rm -rf Module*")
    elif status == "py3":
        functions = {
            0: "generate_order",
            1: "compute_cost",
            2: "simulate_restaurant"
        }
        try:
            os.system("curl -H 'Authorization: token " + github_token + "' -H 'Accept: application/vnd.github.v3.raw' -O -L https://api.github.com/repos/" + repo + "/contents/Module3.ipynb")
        except:
            return
        s = subprocess.run(["python", "Py1Test.py"], capture_output=True)
        s = str(s.stdout.decode("utf-8")).split("\n")[-2]
        eval = json.loads(s)
        if sum(eval) == 3:
            db.child(key_fb_hyouka).child(id).update({"progress": "py3v"})
            tars.chat_postMessage(channel=chat, text="You're almost done with Module 3. Get your plots and simulate_restaurant function verified by a TA, and then move on to the " + group + " Assignments. Terrific work!")
            message = name + " has completed Py3, verify and update progress with TARS."
            tars.chat_postMessage(channel=tars_admin, text=message)
        else:
            check = np.where(np.array(eval) == 0)[0]
            if len(check) != 3:
                if 1 in eval:
                    tars.chat_postMessage(channel=chat, text="You did these right:")
                    for i in range(len(eval)):
                        if eval[i] == 1:
                            tars.chat_postMessage(channel=chat, text=functions[i])
            if len(check) > 0:
                if 0 in eval:
                    tars.chat_postMessage(channel=chat, text="Oops! Please check these functions and try submitting again:")
                    for value in check:
                        tars.chat_postMessage(channel=chat, text=functions[value])
            tars.chat_postMessage(channel=chat, text="Do contact a TA if you have any doubts!")
        os.system("rm -rf Module*")

if __name__ == "__main__":
    app.run(threaded=True)
