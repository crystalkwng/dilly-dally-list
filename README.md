# The Dilly Dally List — beginner setup guide

This is a starter version of a shared adventure list built with Python, Streamlit, and Supabase.

## What it includes
- Add, edit, and delete adventures
- Search, sort, and filter by type, status, and difficulty
- Adventure details: location, distance, difficulty, notes, link, and status
- Optional latitude/longitude for map pins
- Excel/CSV import with column matching
- Shared password gate
- Hosted PostgreSQL storage through Supabase

## Important note about access
This starter uses one shared password for the app. Anyone who has that password can edit or delete entries. It is suitable for a small trusted group, not sensitive information. For individual accounts and different permissions, add Supabase Auth before using it with a larger group. Keep the Supabase service-role key secret; it has powerful database access.

## Part A — Create the database
1. Create a project at https://supabase.com/.
2. Open **SQL Editor** in the Supabase dashboard.
3. Open `supabase_setup.sql` from this project, copy all of it into a new SQL query, and click **Run**.
4. In Supabase Project Settings / API (or Connect), copy the project URL and the service-role key. Labels can vary by dashboard version. Do not share the service-role key.

## Part B — Run locally (optional)
1. Install Python 3.11 or newer from https://www.python.org/downloads/.
2. Open Terminal (Mac) or Command Prompt (Windows), and go to this project folder.
3. Create and activate a virtual environment:
   - Mac: `python3 -m venv .venv` then `source .venv/bin/activate`
   - Windows: `py -m venv .venv` then `.venv\Scripts\activate`
4. Install packages: `python -m pip install -r requirements.txt`
5. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in your own values.
6. Run: `streamlit run app.py`

Never upload `.streamlit/secrets.toml` to GitHub.

## Part C — Deploy online
1. Create/sign in to GitHub at https://github.com/.
2. Create a new repository. Upload `app.py`, `requirements.txt`, `supabase_setup.sql`, and the `.streamlit/secrets.toml.example` file. Do NOT upload your real `secrets.toml`.
3. Visit https://share.streamlit.io/ and connect GitHub.
4. Choose **Create app**, select your repository and `app.py`, then deploy.
5. In the Streamlit app dashboard, open **Settings → Secrets** and paste these values, replacing the examples:

   ```toml
   APP_PASSWORD = "choose-a-long-private-shared-password"
   SUPABASE_URL = "https://YOUR-PROJECT.supabase.co"
   SUPABASE_SERVICE_ROLE_KEY = "YOUR-SUPABASE-SERVICE-ROLE-KEY"
   ```

6. Save the secrets and restart/reboot the app if needed.
7. Share the Streamlit URL and shared password only with the people you want to edit the list.

Official deployment guide: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app
Secrets guide: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management

## Part D — Import your existing hiking spreadsheet
1. Open the deployed app and sign in.
2. Choose **Import list**.
3. Upload `The Hike List.xlsx` or a CSV copy.
4. Match your spreadsheet columns to the app's fields, then click **Import adventures**.
5. Review the list. The importer defaults unrecognized adventure types to Hiking, unrecognized statuses to Want to go, and unrecognized difficulty to Unknown.

## Map pins
The map tab plots entries that have latitude and longitude. The location text and map links still work without coordinates. To find coordinates, open a location in Google Maps, right-click the point, and copy the displayed coordinates; enter latitude and longitude in the add/edit form.

## Backups
Use Supabase's database export/backup features periodically. Before bulk imports or major changes, export a copy of the table. A shared password does not identify which person made each change.
