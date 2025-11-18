## RushMore Pizzeria Enterprise Database System (Azure postgreSQL + python + powerBI)
### Project Overview

RushMore Pizzeria started with a simple Python ordering system using a JSON file as storage. As the business expanded to multiple locations with thousands of customers, JSON became Slow, Prone to corruption,Not scalable, Impossible to query, Not multi-user.
To solve this, I migrated RushMore Pizzeria to a fully-designed PostgreSQL enterprise database deployed in Microsoft Azure, and populated it with 10,000+ rows of realistic, synthetic business data using Python, Faker, and psycopg2, for testing and analysis.

This README provides:

Full system architecture
Database ERD
SQL schema
Python automation (data generation)
Cloud deployment steps
Power BI analytics dashboards 
Screenshots (Azure portal and pgAdmin )

Tech Stack: 

 Azure PostgreSQL     Flexible Server - Cloud database.


Python (psycopg2, Faker, python-dotenv) - Programming

PostgreSQL, Normalization (3NF) - Data Modeling

Visualization  - Power BI 

IDE - VS Code

Admin Tool - pgAdmin 4

Version Control - 	Git + GitHub

## Database Architecture
![alt text](<Rushmore ERD.PNG>)
## Rushmore ERD

## Database Schema Summary
1️⃣ Stores

store_id (PK)

address

city

phone_number

opened_at

2️⃣ Customers

customer_id (PK)

first_name, last_name

email

phone_number

created_at

3️⃣ Ingredients

ingredient_id (PK)

name

stock_quantity

unit

4️⃣ Menu_Items

item_id (PK)

name

category

size

price

5️⃣ Item_Ingredients (composite PK)

item_id (FK)

ingredient_id (FK)

quantity_required

6️⃣ Orders

order_id (PK)

customer_id (FK)

store_id (FK)

order_timestamp

total_amount

status

7️⃣ Order_Items

order_item_id (PK)

order_id (FK)

item_id (FK)

quantity

price_at_time_of_order.

### Analytics Dashboards (Power BI)

Using the Azure cloud database, I built dashboards answering the key business questions.
### Rushmore Dashboard
![alt text](image.png)

### Screenshots
1. Azure PostgreSQL Server
![alt text](<Azure database with postgres.PNG>)

2. pgAdmin – Tables with Row Counts:
(a) Customers table
![alt text](image-1.png)
(b) Ingredients table
![alt text](image-2.png)
(c) Item_ingredient table
![alt text](image-3.png)
(d) Menu_item table
![alt text](image-4.png)
(e) Order_item table
![alt text](image-5.png)
(f) Orders table
![alt text](image-6.png)
(g) Store table
![alt text](image-7.png)
 
 In conclusion, this project demonstrates:

 Professional data modeling (3NF)
 Cloud database deployment (Azure PostgreSQL)
Python Data Engineering with Faker + psycopg2
Foreign key–safe data insertion
Real-world BI dashboards (Power BI)
Scalable enterprise-grade design.

It transforms RushMore Pizzeria from a simple JSON-based prototype into a full enterprise analytics-ready system.