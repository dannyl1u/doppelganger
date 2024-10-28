#!/bin/bash

# Run Ollama
(source .env && if [[ -n "${OLLAMA_MODEL}" ]]; then
  echo "running ollama with ${OLLAMA_MODEL}..."
  ollama run "${OLLAMA_MODEL}"
  fi
  ) &

# Run Flask server in the background
(source .env &&
  if [[ "${ENV}" -neq "DEV" ]]; then
    echo "running the GitHub app"
    python3 app.py
  else
    echo "In development mode. Need to manually run the app.py"
  fi
) &

# Forward localhost to public URL using Ngrok
(source .env && if [[ -n "${NGROK_URL}" ]]; then
  echo "running ngrok with specified url..."
  ngrok http --url "${NGROK_URL}" # --oauth=google  --oauth-allow-email="${GOOGLE_EMAIL}"
  fi
  )
