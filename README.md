# Ride Guardian Desktop Application

This document provides instructions on how to set up and run the Ride Guardian desktop application, converted from the original web application.

## Prerequisites

*   **Python:** Version 3.8 or higher is recommended. You can download Python from [python.org](https://www.python.org/).
*   **pip:** Python's package installer, usually included with Python installations.

## Setup Instructions

1.  **Extract the Application:**
    Unzip the provided `ride_guardian_desktop_app.zip` file to a location of your choice. This will create a `desktop_app` folder containing the application code.

2.  **Navigate to the Directory:**
    Open your terminal or command prompt and navigate into the extracted `desktop_app` folder:
    ```bash
    cd path/to/desktop_app
    ```

3.  **Create a Virtual Environment (Recommended):**
    It's best practice to create a virtual environment to manage dependencies for the project separately.
    ```bash
    python -m venv venv 
    ```
    Activate the virtual environment:
    *   On Windows:
        ```bash
        .\venv\Scripts\activate
        ```
    *   On macOS/Linux:
        ```bash
        source venv/bin/activate
        ```
    You should see `(venv)` at the beginning of your terminal prompt.

4.  **Install Dependencies:**
    Install the required Python libraries using the provided `requirements.txt` file:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

Once the setup is complete, you can run the application using:

```bash
python main.py
```

The application window should appear. The first time you run it, it will automatically create the SQLite database file (`ride_guardian.db`) in the `desktop_app` directory if it doesn't exist.

## Application Structure

*   `main.py`: The main entry point for the application.
*   `requirements.txt`: Lists the required Python packages.
*   `ride_guardian.db`: The SQLite database file (created on first run).
*   `core/`: Contains core logic, including `database.py` for database interactions.
*   `ui/`: Contains the user interface code.
    *   `views/`: Different sections/tabs of the application (Monitoring, Data Import, Payroll, Rules, Reports).
    *   `widgets/`: Reusable custom UI components (if any were created).
*   `assets/`: For storing application assets like icons (currently unused).

## Features

*   **Data Import:** Import ride data from Excel files (.xlsx, .xls).
*   **Ride Monitoring:** View and filter ride data with status indicators.
*   **Rule Configuration:** Set rules for distance, time, bonuses, and pay.
*   **Payroll Calculator:** Calculate payroll based on rides and rules, with export options.
*   **Reports & Analytics:** View performance KPIs, charts (revenue trend, driver performance, hourly distribution, compliance), and export reports.

## Notes

*   The application uses SQLite for data storage. The database file `ride_guardian.db` will be created in the same directory as `main.py`.
*   The UI is functional but follows the prompt's instruction not to replicate the exact web UI aesthetics.
*   Payroll calculation logic is based on the provided prompts and may need refinement based on specific business rules (e.g., how hours are calculated from rides).
*   Ensure you have appropriate permissions to read/write files in the application directory (for database creation and exports).

