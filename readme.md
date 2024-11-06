# Fall 2024 Capstone Project

This application is the Fall 2024 capstone project of:
- **Sulaiman Mulla** - <sulaiman_1@tamu.edu>
- **Sathvik Yeruva** - <sryeruva@tamu.edu>
- **Maria Viteri** - <mev@tamu.edu>
- **Alec Klem** - <alecklem@tamu.edu>

## How to Set Up

1. **Clone the Repository**:  
   After cloning, run the `setup_venv.sh` script:
   - This will create a virtual environment, install pip, and install all dependencies from `requirements.txt`.
   - Once the script completes, activate the environment by running:
     ```bash
     source venv/bin/activate
     ```

2. **Database Setup**:  
   Run the `db_reset.sh` script to create the SQLite database (used tentatively).  
   - Running this script will reset (empty) the database if it already exists.

3. **Run Tests**:  
   Run the `run_tests.sh` script to:
   - Set the Python path
   - Run tests
   - Generate HTML coverage report

   ```bash
   ./run_tests.sh
