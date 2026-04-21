# Setting Up Gmail API for Order Notifications

To enable the automated vendor emails, you need to configure the Gmail API in your Google Cloud account and provide the credentials to the backend.

### Step 1: Create a Google Cloud Project
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Click on the project dropdown and select **"New Project"**.
3. Name it (e.g., `MetroHardware-OMS`) and click **Create**.

### Step 2: Enable the Gmail API
1. In the sidebar, go to **APIs & Services > Library**.
2. Search for **"Gmail API"** and click on it.
3. Click **Enable**.

### Step 3: Configure the OAuth Consent Screen
1. Go to **APIs & Services > OAuth consent screen**.
2. Choose **External** (unless you have a Workspace organization) and click **Create**.
3. Fill in the required app information (App name, User support email, Developer contact info).
4. Click **Save and Continue** until you reach the dashboard.
5. In the "Test users" section, click **Add Users** and add the Gmail address you will use to send the emails.

### Step 4: Create OAuth 2.0 Credentials
1. Go to **APIs & Services > Credentials**.
2. Click **Create Credentials > OAuth client ID**.
3. Select **Desktop app** as the Application type.
4. Name it (e.g., `Backend Desktop Client`) and click **Create**.
5. A dialog will show your Client ID and Client Secret. Click **Download JSON**.
6. Rename the downloaded file to `credentials.json` and move it to the `backend/` directory of this project.

### Step 5: Initial Authentication
1. Ensure you have the dependencies installed: `pip install -r requirements.txt`.
2. When you place the first order in the internal portal, the backend will attempt to authenticate.
3. A browser window will open asking you to log in to your Google account.
4. Since the app is not verified, you may need to click **Advanced > Go to [App Name] (unsafe)**.
5. Grant the permissions requested.
6. Once complete, a `token.json` file will be created in the `backend/` directory. This file stores your login session so you won't have to log in again.

> [!WARNING]
> Both `credentials.json` and `token.json` contain sensitive information. **Do not share them or commit them to public repositories.** They are already ignored by `.gitignore` in this project.
