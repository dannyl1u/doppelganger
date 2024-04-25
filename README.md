# doppelgänger
<ins>problem:</ins> open-source maintainers spend a lot of time managing duplicate/related (doppelgänger) issues & pull requests  
<ins>solution:</ins> doppelgänger compares newly submitted issues/prs against existing ones to automatically flag duplicate/related (doppelgänger) issues/prs

**topics: vector db, github, open-source, embedding search, rag, similarity scores**

Requirements

- Python 3.6 or later
- Flask

Setup

1. Clone this repository to your local machine:

   `git clone https://github.com/dannyl1u/doppelganger.git`
   `cd doppelganger`

2. Create a virtual environment and install dependencies:

   python -m venv venv
   source venv/bin/activate  # Use `venv\Scripts\activate` on Windows
   pip install -r requirements.txt

3. Run the Flask server:

   python app.py

4. Configure a GitHub Webhook:

   - Go to your GitHub repository settings
   - Navigate to "Webhooks" and click "Add webhook"
   - Enter the following details:
     - Payload URL: `https://your-public-url/webhook`
     - Content type: `application/json`
     - Which events would you like to trigger this webhook?: Select "Let me select individual events" and check "Issues" and "Pull requests"
   - Click "Add webhook"

Using the Bot

After completing the setup, the bot will listen for events from GitHub. You can observe the logs in your terminal to confirm that the bot is receiving and processing events correctly. This project can be extended to perform additional actions upon receiving pull requests or issues.

Notes

- To make your Flask server publicly accessible, consider using a tool like [ngrok](https://ngrok.com/) to expose it to the internet during development.
- Ensure proper security measures for the webhook endpoint to avoid unauthorized access or potential attacks.
