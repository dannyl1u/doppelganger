# doppelgänger
<ins>Problem:</ins> open-source maintainers spend a lot of time managing duplicate/related (doppelgänger) issues & pull requests  
<ins>Solution:</ins> doppelgänger compares newly submitted issues/PRs against existing ones to automatically flag duplicate/related (doppelgänger) issues/PRs

**Topics: vector db, github, open-source, embedding search, rag, similarity scores**

https://github.com/dannyl1u/doppelganger/assets/45186464/cdc1c68b-4241-43d9-806c-b4b5cc1a702d

## Setup

1. Clone this repository to your local machine:

   ```
   git clone https://github.com/dannyl1u/doppelganger.git
   cd doppelganger
   ```
2. Build Docker image and run:

   ```
   docker build -t doppelganger . && docker run --name doppelganger doppelganger
   ```

or 

2. Create a virtual environment and install dependencies:

   - `python -m venv venv`
   - `source venv/bin/activate`  # Use `venv\Scripts\activate` on Windows
   - `pip install -r requirements.txt`

3. Run the Flask server:

   ```
   python app.py
   ```

4. Configure a GitHub App Webhook:

- Go to your GitHub account settings and navigate to "Developer settings" > "GitHub Apps".
- Click "New GitHub App" or select your existing GitHub App.
- Under "Webhook URL", enter the following URL: `https://your-public-url/webhook`.
- Set the "Webhook secret" to match the value in your `.env` file (`WEBHOOK_SECRET`).
- Under "Permissions & events", ensure the app has the necessary permissions:
  - Repository permissions: `Read & Write` for `Issues` and `Pull requests`.
  - Subscribe to events: Check "Issues" and "Pull requests".
- Click "Create GitHub App" or "Save changes".
- Install the GitHub App on the target repository by navigating to the "Install App" section and selecting the repository.

## Notes

- To make your Flask server publicly accessible, consider using a tool like [ngrok](https://ngrok.com/) to expose it to the internet during development.
- Ensure proper security measures for the webhook endpoint to avoid unauthorized access or potential attacks.

## Star History

<a href="https://star-history.com/#dannyl1u/doppelganger&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=dannyl1u/doppelganger&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=dannyl1u/doppelganger&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=dannyl1u/doppelganger&type=Date" />
  </picture>
</a>
