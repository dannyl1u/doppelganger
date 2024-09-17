# doppelgänger
<ins>Problem:</ins> open-source maintainers spend a lot of time managing duplicate/related (doppelgänger) issues & pull requests  
<ins>Solution:</ins> doppelgänger compares newly submitted issues/PRs against existing ones to automatically flag duplicate/related (doppelgänger) issues/PRs

**Topics: vector db, github, open-source, embedding search, rag, similarity scores**

https://github.com/dannyl1u/doppelganger/assets/45186464/cdc1c68b-4241-43d9-806c-b4b5cc1a702d

This application is a GitHub App that automatically compares newly opened issues with existing ones, closing and commenting on highly similar issues to reduce duplication.

## Prerequisites

- Python 3.7+
- A GitHub account
- A server or hosting platform to run the app (e.g., Heroku, DigitalOcean, AWS)

## Setup Instructions

### 1. Create a GitHub App

1. Go to your GitHub account settings.
2. Click on "Developer settings" in the left sidebar.
3. Select "GitHub Apps" and click "New GitHub App".
4. Fill in the required information:
   - GitHub App name: Choose a unique name (e.g., "Issue Similarity Checker")
   - Homepage URL: Your app's website or your GitHub profile
   - Webhook URL: The URL where your server will be running (e.g., https://your-server.com/webhook)
   - Webhook secret: Generate a secure secret and save it for later use
5. Set permissions:
   - Repository permissions:
     - Issues: Read & write
     - Pull requests: Read & Write
     - Webhooks: Read-only
   - Subscribe to events:
     - Issues
     - Pull request
6. Create the app and note down the App ID
7. Generate a private key and download it (you'll need this later)

### 2. Prepare Your Environment

1. Clone this repository:
   ```
   git clone https://github.com/dannyl1u/doppelganger.git
   cd doppelganger
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with the following content:
   ```
   APP_ID=your_app_id_here
   WEBHOOK_SECRET=your_webhook_secret_here
   ```

4. Place the downloaded private key in the project root and name it `rsa.pem`.

### 3. Deploy the Application

1. Choose a hosting platform (e.g., Heroku, DigitalOcean, AWS) and follow their deployment instructions.
2. Make sure your server is accessible via HTTPS.
3. Set the environment variables (`APP_ID`, `WEBHOOK_SECRET`) on your hosting platform.
4. Upload the `rsa.pem` file to your server (ensure it's not publicly accessible).

### 4. Update GitHub App Settings

1. Go back to your GitHub App settings.
2. Update the Webhook URL to point to your deployed application (e.g., https://your-server.com/webhook).

### 5. Install the GitHub App

1. Go to your GitHub App's settings page.
2. In the "Install App" section, click "Install App" or "Add Installation".
3. Choose the account where you want to install the app.
4. Select the repository (or repositories) where you want to use the app.
5. Confirm the installation.

## Usage

Once installed, the app will automatically:

1. Monitor new issues and PRs in the selected repositories.
2. Compare new issues and PRs with existing ones using semantic similarity.
3. Close and comment on highly similar issues and PRs to reduce duplication.

## Configuration

You can adjust the similarity threshold by modifying the `SIMILARITY_THRESHOLD` variable in the script. The default is set to 0.5.

## Troubleshooting

- Check the server logs for any error messages.
- Ensure all environment variables are correctly set.
- Verify that the `rsa.pem` file is present and correctly formatted.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Star History

<a href="https://star-history.com/#dannyl1u/doppelganger&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=dannyl1u/doppelganger&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=dannyl1u/doppelganger&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=dannyl1u/doppelganger&type=Date" />
  </picture>
</a>
