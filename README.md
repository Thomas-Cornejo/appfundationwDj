<h1 align="center">Fundation Web App</h1>

<p align="left">
   <img src="https://img.shields.io/badge/STATUS-IN%20DEVELOPMENT-blue">
</p>

### Description
This web application is designed to modernize and improve the digital ecosystem of animal foundations in Cúcuta, Norte de Santander (Colombia). It streamlines the management of adoptions, sponsorships, donations, and animal registrations, providing users and administrators with an intuitive, efficient, and engaging experience.

The application introduces a gamified sponsorship system, where users can support animals through contributions that grant rewards, track progress, and interact with the community, thus promoting responsible pet ownership and strengthening the bond between the community and rescued animals.

With a focus on usability, transparency, and automation, the system allows foundations to centralize their operations, optimize internal workflows, and streamline their processes.

---

### Technologies Used

- **Python 3.12.3**
- **Django**
- **HTML5**
- **JavaScript**
- **Tailwind CSS**
- **Cloudinary (media storage)**
- **PostgreSQL**

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
- Animal detail view (public)
- Adoption request flow (user-side)
- Refined history display (user-friendly version)
- Sponsorship module with gamification system
- User dashboard with progress and rewards
- Admin dashboard with analytics and activity tracking
- Notification system (email, push, in-app)
- Donation system integration with Wompi payment gateway
- Code quality monitoring system with automated indicator degradation
- Automated cron job for quality indicators maintenance

### 🔜 Planned / Next Steps
- "Help Us" section (donation campaigns and volunteer management)
- Enhanced gamification features
- Mobile app integration
- Advanced analytics and reporting

---

## Available Commands

The project includes several custom scripts and management commands:

### Create Superuser
```bash
python manage.py create_superuser
```
Creates an admin user with predefined credentials (check the script for details).

### Code Quality Compliance Check
```bash
python scripts/calculate_compliance.py
```
**Important:** This script calculates and reports code quality metrics compliance based on project standards:
- **Pylint score:** Must be ≥ 8.0/10
- **Test coverage:** Must be ≥ 90%
- **Code complexity:** Must be maintained within acceptable limits

Use this command before committing to ensure your code meets quality standards.

### Degrade Indicators
```bash
python scripts/degrade_indicators.py
```
This script automatically degrades quality indicators over time. It is designed to be executed via cron job daily.

---

## Automated Tasks (Cron Jobs)

The application uses a cron job to maintain quality indicators:

### Configured Cron Job:

**Degrade Indicators** (Daily at 12:00 AM)
```bash
python scripts/degrade_indicators.py
```
Automatically degrades quality indicators to encourage continuous improvement and prevent stale metrics.
