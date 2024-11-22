Here’s the full updated README document with all the requested changes:  

---

# Fall 2024 Capstone Project  

This application is the Fall 2024 capstone project of:  
- **Sulaiman Mulla** - <sulaiman_1@tamu.edu>  
- **Sathvik Yeruva** - <sryeruva@tamu.edu>  
- **Maria Viteri** - <mev@tamu.edu>  
- **Alec Klem** - <alecklem@tamu.edu>  

---

## Introduction  

This project is a pure Python application built using the Reflex framework. It incorporates Google OAuth for authentication, with special admin privileges available for tasks such as repopulating the database and retraining the model. To gain admin access, contact one of the developers listed above.  

---

## Requirements  

### Environment  
- Python 3.12.3  

### External Dependencies  
- Reflex Framework (Automatically handled via `requirements.txt`)  
- Google OAuth  

---

## How to Set Up  

### Step 1: Clone the Repository  
Clone the repository and set up the environment:  

```bash
git clone https://github.com/your-repo-name.git
cd your-repo-name
```

### Step 2: Set Up the Virtual Environment  
Run the `setup_venv.sh` script to create a virtual environment, install pip, and install dependencies:  

```bash
./setup_venv.sh
```

Activate the virtual environment:  
```bash
source venv/bin/activate
```

When done, deactivate the environment with:  
```bash
deactivate
```

### Step 3: Run Tests  
Run the `run_tests.sh` script to set the Python path, execute tests, and generate an HTML coverage report:  

```bash
./run_tests.sh
```

### Step 4: Run the App  
1. Navigate to the app directory:  
   ```bash
   cd app
   ```

2. Initialize Reflex:  
   ```bash
   reflex init
   ```

3. Run the app:  
   ```bash
   reflex run
   ```

**Important**: Always run Reflex commands inside the `app` directory to avoid creating unintended Reflex apps.  

---

## Tests  

Our test suite is included in the repository and can be executed as follows:  

```bash
./run_tests.sh
```

This will generate an HTML report for test coverage.  

---

## Adding an API  

To add a new API to the project:  

1. Navigate to the `database/APIs` directory.  
2. Create a new folder for the specific API you want to add.  
3. Inside that folder, create a wrapper file for the API.  
4. Follow the format and conventions used in existing API wrapper files within the `apis` directory as a reference.  

---

## Support  

For any inquiries or further development, contact one of the developers listed at the beginning of this document.  

---

## CI/CD  

Our CI/CD pipeline ensures rigorous testing and integration. GitHub Actions workflows can be found in the repository.  

---

## References  

- [Reflex Documentation](https://reflex.dev/docs)  
- [Google OAuth Setup Guide](https://developers.google.com/identity/sign-in/web/sign-in)  
- [How to Set Up Virtual Environments](https://docs.python.org/3/library/venv.html)  

