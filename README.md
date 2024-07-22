# MedicalResidentScheduling

Postgraduate medical students need to complete additional training to become physicians. Depending on their study program, students are required to take various courses, not all of which are available at every hospital. Consequently, these students must be assigned to hospitals where they can both work and further their studies.

Historically, this assignment process has been managed manually, which is time-consuming and prone to errors. There is a clear need to automate and digitalize the scheduling process to improve efficiency and accuracy. Additionally, the schedule must be flexible enough to accommodate changes due to sickness, vacation, or other unforeseen circumstances.
The Solution

The Medical Resident Scheduling Software offers a robust solution for creating feasible and efficient schedules for medical residents. At the core of this software is an integer linear programming algorithm, which generates an optimal schedule based on predefined constraints and requirements.

Key Features:

1. Automated Scheduling: Eliminates the need for manual scheduling, saving time and reducing errors.
2. Flexibility: The algorithm can be adjusted to produce strict or more flexible schedules, catering to different needs and scenarios.
3. Dynamic Re-adjustments: Easily modify the schedule to accommodate changes such as sickness or vacation.

For a more detailed overview of how the algorithm works and its capabilities, please refer to the poster (Poster.pdf).

This software aims to streamline the scheduling process, ensuring that postgraduate medical students can efficiently complete their training while meeting all program requirements.

# Install and Run the Project

The project requires a Docker environment for execution.
Follow these steps to set up the Docker environment for the project:

1. **Install Docker Desktop and docker-compose**:

   [Docker Desktop](https://docs.docker.com/compose/install/) needs to be installed. This includes docker-compose as well.

2. **Clone the Repository**:

```bash
git clone https://github.com/CombiRWTH/MedicalResidentScheduling.git
cd MedicalResidentScheduling
```

3. **Gurobi Web License Service (WLS) Setup**:

To run the algorithm, you will need a [Gurobi Web License Service (WLS) License](https://www.gurobi.com/features/web-license-service/).
You can also opt for an [Academic WLS License](https://www.gurobi.com/features/academic-wls-license/) if eligible.
Once you have obtained your license, create a file named gurobi.env in the base directory with the following content:

```
WLSACCESSID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
WLSSECRET=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
LICENSEID=99999
```

Replace the placeholders (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx and 99999) with your actual license details, which you can find in the downloaded gurobi.lic file.

**Important**: Please never share your private keys.

3. **Preparation to run Docker Compose**:

   Make sure the line break types of the script 'create_second_db.sh' are set to LF (Line Feed) instead of CRLF (Carriage Return Line Feed).
   If the line breaks are not in LF format, force the update by running the following commands:

   ```bash
   git rm -rf --cached .
   git reset --hard HEAD
   ```

4. **Run Docker Compose**:

   ```bash
   docker-compose up -d
   ```

   This command should be executed in the root file directory.

5. **Access the Application**:
   Once the Docker containers are running, access the application through your web browser at http://localhost:8080.

# Technology Stack

This project leverages several key technologies to deliver a powerful and efficient solution:

- [Docker](https://www.docker.com/): Provides a containerized environment to ensure consistent execution across different systems and simplifies development and deployment.
- [PostgreSQL](https://www.postgresql.org): Serves as the robust relational database management system used to store and manage all scheduling data.
- [Django](https://www.djangoproject.com/): A high-level Python web framework that enables rapid development of secure and maintainable web applications.
- [Gurobi](https://www.gurobi.com/): Utilized for its state-of-the-art optimization capabilities, Gurobi solves the integer linear programming problems efficiently.
  - You have to install a [WLS License](https://www.gurobi.com/features/web-license-service/) ([Academic License](https://www.gurobi.com/features/academic-wls-license/)) in order to use Gurobi for the execution of an evaluation
- [Python](https://www.python.org/): The core programming language used for developing the algorithm and the web application, chosen for its readability and extensive libraries.

# Function Overview

## Students

1. [Input of priorities](http://localhost:8080/student/)

   Allows students to enter their preferences and priorities for hospital assignments and courses.

2. [Input of absence](http://localhost:8080/create_student_ausfall/)

   Enables students to report planned absences such as vacations or other leave periods.

3. [Evaluation of results](http://localhost:8080/serg/)

   Provides students with the ability to view and evaluate their assigned schedule.

## Admins

1. [Input hospital](http://localhost:8080/admin-page/)

   Allows administrators to input new hospitals into the system.

2. [View / edit hospitals](http://localhost:8080/adminaktuell/)

   Enables administrators to view and edit the details of existing hospitals.

3. [Import / Export of databases](http://localhost:8080/import_export/)

   Facilitates the import and export of the database model for backup or migration purposes in json. Test data is provided in the folder example_data.

4. [Start evaluation with input of parameters](http://localhost:8080/aerg/)

   Allows administrators to initiate the scheduling planning process with specific parameters.

5. [Evaluation display in detail](http://localhost:8080/detailansicht_auswertung/)

   Provides a detailed view of the scheduling evaluation results for in-depth analysis.

6. [Evaluation display with colored blocks](http://localhost:8080/bloecke_auswertung/)

   Shows the evaluation results using a color-coded block format for easy visualization.

## General

1. [Info page](http://localhost:8080/)

   General information about the application and its usage.

2. [Registration](http://localhost:8080/registration/) / [Login](http://localhost:8080/login/)

   Allows new users to register for an account and existing users to log in.

3. [Django admin](http://127.0.0.1:8080/admin/)

   Create a user who can login to the admin site:
   docker-compose run web python manage.py createsuperuser

   Django Admin is a built-in interface in the Django framework that automatically generates a web-based administrative interface for managing data models.
   It supports features like user authentication, customizable model representation, filtering, searching, and bulk actions, making it a powerful tool for efficient data management.

# Developer notes

## Database design

The application utilizes two databases (refer to 'DATABASES' in `mrs/settings.py`). The primary database contains the complete app data, while the secondary database holds only the data model.
This setup supports both a live and a test database, with import operations permitted only on the test database. You can modify this configuration using the Import/Export tool.

## API Documentation

**Overview**

The API is implemented with the tool [django-rest-framework](https://www.django-rest-framework.org/).
This API provides the following endpoints for CRUD operations on all models. The primary key (pk) used in the endpoints refers to the unique identifier (id) of the model.

- List

  - Description: Retrieve a list of all records.
  - Method: GET
  - Endpoint: /api/{modelname}/

- Retrieve

  - Description: Retrieve a specific record by its primary key.
  - Method: GET
  - Endpoint: /api/{modelname}/{pk}/

- Create

  - Description: Create a new record.
  - Method: POST
  - Endpoint: /api/{modelname}/

- Update

  - Description: Update an existing record. This request validates all fields of the model.
  - Method: PUT
  - Endpoint: /api/{modelname}/{pk}/

- Partial Update

  - Description: Partially update an existing record. This request does not validate fields; you can send only the fields you want to change.
  - Method: PATCH
  - Endpoint: /api/{modelname}/{pk}/

- Delete

  - Description: Delete an existing record.
  - Method: DELETE
  - Endpoint: /api/{modelname}/{pk}/

**Available Models**

All available models can be accessed at: http://127.0.0.1:8080/api/.

**Notes on GET Requests**

GET requests may contain foreign keys to related data. For example, a GET request to /api/organisationsgruppen/105/ might return the following data:

```json
{
  "id": 105,
  "ausbildungsstaette_set": [409, 410, 411],
  "dienstposten_set": [1529, 1530],
  "id_ext": 737,
  "is_kooperationspartner": true,
  "name": "Krankenhaus 1"
}
```

In this response:

- ausbildungsstaette_set and dienstposten_set are arrays of primary keys from their respective tables.

To retrieve a related record, you can use the primary key provided. For example, to retrieve the related ausbildungsstaette record with id 409, you would call:

- GET: /api/ausbildungsstaette/409/

## Add new migrations

1. Change your models (in models.py).
2. Run docker-compose run web python manage.py to create migrations for those changes
3. Run docker-compose run web python manage.py migrate --database=only_datamodel to apply those changes to the database.

Official django documentation: https://docs.djangoproject.com/en/5.0/topics/migrations/

# Credits

Clemens Queckenberg, Dennis John, Felix Britzelmaier, Gaser Abdelaziz, Henning Erdweg, Luke Dreßen, Lynn Clemens, Simon
Schürmann, Svenja Westphal, Theresa Täuber, Timothy Müller

# Contributing

We welcome contributions from the community. If you would like to contribute, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Commit your changes and push the branch to your fork.
4. Open a pull request with a detailed description of your changes.

# License

This project is licensed under the MIT License. See the LICENSE file for more details
