# TrekCentral

TrekCentral is a role-based trekking management web application built with Flask. It allows users to explore available treks, make and manage bookings, and view their booking history. Staff members can manage assigned treks and bookings, while administrators can manage treks, staff approvals, and user access.

## Key Features

### User
- User registration and login
- Browse available treks and view trek details
- Book a trek
- Cancel bookings
- View booking history
- Prevent overbooking of treks
- Manage profile information

### Trek Staff
- Staff registration
- Staff approval by administrators
- View assigned treks
- Manage trek-related bookings
- Manage staff profile

### Administrator
- Admin authentication
- Create, update, and delete treks
- Manage trek details and availability
- Assign staff members to treks
- Approve or reject staff registrations
- Blacklist or remove access for users and staff
- Manage users, staff, treks, and bookings

## Tech Stack

- **Backend:** Python, Flask
- **Frontend:** HTML, Jinja2, Bootstrap 5
- **Database:** SQLite
- **ORM:** Flask-SQLAlchemy / SQLAlchemy
- **Authentication:** Flask-Login
- **Configuration:** python-dotenv

## Project Structure

```text
trekking-management-project/
│
├── templates/
│   ├── admin/
│   ├── staff/
│   └── users/
│
├── static/
│   └── trek_images/
│
├── app.py
├── config.py
├── models.py
├── routes.py
├── requirements.txt
├── .env.sample
├── .gitignore
└── README.md
```

## Installation
**1. Clone the repository**
```
git clone <repository-url>
cd trekking-management-project
```
**2. Create a virtual environment**

*Windows*
```
python -m venv venv
.\venv\Scripts\activate
```
*macOS / Linux*
```
python3 -m venv venv
source venv/bin/activate
```
**3. Install dependencies**
```
pip install -r requirements.txt
```
**4. Configure environment variables**

Create a .env file from the provided .env.sample:

*macOS / Linux*
```
cp .env.sample .env
```
*Windows*
```
copy .env.sample .env
```


Update the values in .env with your local configuration, including the database URI, secret key, and administrator credentials.

`Never commit your .env file or real credentials to the repository.`

**5. Run the application**
```
flask run
```
*Note:- Dont use `python app.py`*
The application will be available at:

```
http://127.0.0.1:5000
```
**Environment Variables**

The application uses environment variables for configuration and sensitive credentials.

Example:

```
FLASK_DEBUG=false
FLASK_APP=app.py
SQLALCHEMY_DATABASE_URI=sqlite:///db.sqlite3
SQLALCHEMY_TRACK_MODIFICATIONS=false
SECRET_KEY=your_secret_key_here

ADMIN_USERNAME=admin
ADMIN_PHONE=0000000000
ADMIN_PASSWORD=your_admin_password_here
```

Do not use the example values for production deployments.

## Application Roles

TrekCentral uses role-based access control with three primary roles:

| Role | Responsibilities |
|------|------------------|
| **User** | Browse treks, make bookings, cancel bookings, and view booking history |
| **Staff** | Manage assigned treks and related bookings |
| **Admin** | Manage treks, users, staff approvals, assignments, and access control |

## Screenshots
<img width="1920" height="1080" alt="admin dashboard" src="https://github.com/user-attachments/assets/b0946f84-111b-40ea-9036-bf65585db8ed" />
<img width="1920" height="1080" alt="booking history" src="https://github.com/user-attachments/assets/8bdd66c9-b496-4593-aad5-a97393a797c1" />
<img width="1920" height="1080" alt="staff list" src="https://github.com/user-attachments/assets/b020adc9-8f1c-4137-9bfb-42e046b97fc4" />
<img width="1920" height="1991" alt="user home page" src="https://github.com/user-attachments/assets/d3237759-caad-4e22-8717-fe310287a45f" />
<img width="1920" height="1895" alt="staff dahsboard" src="https://github.com/user-attachments/assets/3ed6ec1a-88f5-448a-b057-12295b0e94b7" />
<img width="1920" height="1080" alt="staff trek manage" src="https://github.com/user-attachments/assets/4eab45c8-929e-4d33-bfd3-9a6277ff89e1" />



## Notes

This project was developed as a full-stack web application using Flask and server-side rendering with Jinja2. The application demonstrates role-based authentication, database relationships, booking management, CRUD operations, and access control.

## License

This project is intended for educational and portfolio purposes.
![Uploading admin dashboard.png…]()
