<h1 align="center">Fundation Web App</h1>

<p align="left">
   <img src="https://img.shields.io/badge/STATUS-IN%20DEVELOPMENT-blue">
</p>

### Description
A web application designed to optimize the adoption and sponsorship processes for animal foundations located in Cúcuta, Norte de Santander (Colombia).  
It introduces innovation through a **gamified sponsorship system**, improving user engagement and promoting responsible ownership via interactive strategies.

---

### Technologies Used

- **Python 3.12.3**
- **Django**
- **HTML5**
- **JavaScript**
- **Tailwind CSS**
- **Cloudinary (media storage)**

---

### Local Installation & Execution

#### Requirements

Before running the project, make sure you have installed:

- **Python 3.12+**
- **Django** (will be installed automatically from `requirements.txt`)

---

#### Clone the repository

```
git clone https://github.com/Thomas-Cornejo/appfundationwDj.git
cd appfundationwDj
```

#### Create and activate the virtual environment

Create virtual environment
`$ python -m venv .venv`

Activate on Windows
`$ .\venv\Scripts\activate`

Activate on macOS/Linux
`$ source venv/bin/activate`


#### Install dependencies

`$ pip install -r requirements.txt`

#### Install dev tools (linting, testing, etc.)

`$ pip install -r requirements-dev.txt`

#### Configure environment variables

Create a .env file at the project root and set the required variables.

#### Run migrations

`$ python manage.py makemigrations`
`$ python manage.py migrate`

#### Run the server in local

`$ python manage.py runserver `

## Project Roadmap

### 🆗 Completed
- User registration and login system
- Admin panel for creating and managing animals
- Animal history model implemented
- Basic views for browsing available animals with filters

### 🚧 In Progress
- Animal detail view (public)
- Adoption request flow (user-side)
- Refined history display (user-friendly version)

### 🔜 Planned / Next Steps
- Sponsorship module
- Gamification system for sponsors
- Donation system (monetary and in-kind)
- User dashboard with progress and rewards
- Admin dashboard with analytics and activity tracking