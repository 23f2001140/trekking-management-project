# TrekCentral

TrekCentral is a web application that allows users to book a trek, and the assigned staff member will guide them through the trek. The application also allows the user to view the list of available treks and the details of each trek. And on top it There is a Admin who manage everything , Add new treks, delete treks, edit treks, Approve staff registration.,Blacklist users/staff etc.

## Installation

1. Create a virtual environment
2. Install the required dependencies
3. Enviroment setup
4. Run the application


### Create a virtual environment

```bash
python3 -m venv venv
```

### Activate the virtual environment

```bash
source venv/bin/activate (on mac and linux)
.\venv\Scripts\activate (on windows)
```

### Install the required dependencies

```bash
pip install -r requirements.txt
```

### Enviroment setup

```bash
cp .env.example .env
```

Fill in the values for the environment variables in the `.env` file. fill own value for `SECRET_KEY`

### Run the application

```bash
flask run
```
