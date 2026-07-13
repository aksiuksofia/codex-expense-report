# Streamlit Community Cloud deployment

Use this file as a short deployment checklist.

## Main app file

```text
src/app.py
```

## App mode

For the published demo, set this environment variable in the deployment
settings:

```text
APP_MODE=cloud
```

If `APP_MODE` is not set, the app uses local persistent mode by default.

## Dependencies

Streamlit Community Cloud installs Python packages from:

```text
requirements.txt
```

## Secrets

This project does not need secrets for the demo deployment.

Do not commit `.streamlit/secrets.toml`.

## Demo behavior

In cloud demo mode, the app:

- lets users upload CSV files;
- lets users load `data/demo_expenses.csv`;
- analyzes data from the current session;
- lets users compare periods from the current session;
- lets users download Excel reports;
- warns that data may not persist after the app restarts.
