from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/run-script', methods=['GET'])
def run_script():
    # Your Python logic here, for example:
    result = {"message": "Hello, this is the result from your Python script!"}
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
