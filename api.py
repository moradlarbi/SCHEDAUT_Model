from flask import Flask, jsonify
from scheduler import generate_schedule

app = Flask(__name__)

@app.route('/generate_schedule', methods=['GET'])
def generate_schedule_api():
    try:
        schedule_df = generate_schedule()
        return schedule_df.to_json(orient='records'), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
