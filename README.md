# PendoSmart Manual Setup

A web app for evaluating smartling strings with LLM-powered scoring.

## Backend Setup (FastAPI)

1. **Install dependencies:**

   ```sh
   cd backend
   pip install -r requirements.txt
   ```

2. **Run the backend server:**

   ```sh
   ./run_backend.sh
   ```

   (This script runs `uvicorn main:app --host 0.0.0.0 --port 8000`)

   The backend will be available at [http://localhost:8000](http://localhost:8000).

---

## Frontend Setup (Vue 3 + Vite)

1. **Install dependencies:**

   ```sh
   cd frontend
   npm install
   ```

2. **Run the frontend dev server:**

   ```sh
   npm run dev
   ```

   The frontend will be available at the URL shown in your terminal (typically [http://localhost:5173](http://localhost:5173)).

---

## Usage

- Open the frontend in your browser.
- View translation strings.
- Click "Evaluate" to score a translation using the LLM.
- The score and reason will appear in the table and be saved to the database.

---

## Notes
- The Docker compose setup is currently broken and will not work. TODO: WIP
- The backend loads a large language model on startup; first load may take time.
- Database is stored in `backend/strings.db` (SQLite).
- For production, consider using a persistent database and a model server.

---

## Setup

1. **Start Backend and Frontend**
   - Run the backend (`./run_backend.sh`) and frontend (`npm run dev` in `frontend`).

2. **Admin: Set Smartling API Credentials**
   - Go to the admin screen.
   - Enter your Smartling API credentials. See: https://api-reference.smartling.com/#tag/Authentication

3. **Fetch API Token**
   - Use the admin screen to fetch your Smartling API token.
   - Choose the project and locale you want to fetch. eg: ja-jp etc

4. **Fetch Strings**
   - Fetching strings from Smartling may take a while. Please be patient.

5. **View and Manage Strings**
   - Once strings are fetched, go to the main screen to see the table of translations.
   - You cannot edit strings in the app (Smartling API limitation) If you notice anything odd, click the hashcode in the table to open the string directly in Smartling and edit it there.

6. **Evaluate Translations**
   - You can use the local LLM (phi4mini) to evaluate a string if it's a valid translation by clicking the Evaluate button.
