from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def github_webhook():
    data = request.json
    event_type = request.headers.get('X-GitHub-Event', 'ping')

    if event_type == 'pull_request':
        action = data.get('action')
        pr_number = data['pull_request']['number']
        if action == 'opened':
            print(f'New PR opened: {pr_number}')

    elif event_type == 'issues':
        action = data.get('action')
        issue_number = data['issue']['number']
        if action == 'opened':
            print(f'New issue opened: {issue_number}')

    return jsonify({'status': 'success'}), 200

if __name__ == '__main__':
    app.run(port=5000)