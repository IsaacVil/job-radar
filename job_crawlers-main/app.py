from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request
from flask_cors import CORS

from crawlers.common import get_country
from job_check import check_new_job

CHECK_INTERVAL_MINUTES = 15

app = Flask(__name__)
CORS(app)  # Enable CORS on all routes
scheduler = BackgroundScheduler()


@app.route('/check_new_job', methods=['GET'])
def handle_check_new_job():
    check_new_job(request.args.get("email"))
    return {"message": "Job check complete"}, 200


def schedule_job_checks(receiverEmail):
    if not scheduler.running:
        scheduler.start()
    # Replace the job instead of stacking a new one every time the frontend calls /main,
    # and run the first check right away instead of waiting a full interval
    scheduler.add_job(
        check_new_job,
        'interval',
        minutes=CHECK_INTERVAL_MINUTES,
        args=[receiverEmail],
        id="check_new_job",
        replace_existing=True,
        next_run_time=datetime.now()
    )


@app.route('/main', methods=['POST'])  # Change to POST to accept data
def handle_check_periodically():
    data = request.get_json()  # Get JSON data from frontend request
    receiver_email = data.get("email")  # Extract the email from the request
    print("Received email: ", receiver_email)

    if not receiver_email:
        return {"error": "Email is required"}, 400  # Return error if email is missing

    schedule_job_checks(receiver_email)
    return {
        "message": f"Scheduled {get_country()} job checks every {CHECK_INTERVAL_MINUTES} minutes for {receiver_email}"
    }, 200


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
