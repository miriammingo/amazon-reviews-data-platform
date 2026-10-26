# Amazon Reviews Data Platform 🗄️

This project develops a **hybrid data platform for Amazon Reviews**, combining relational, document-oriented and graph databases to store, analyse and explore review data.

The system integrates **MySQL, MongoDB and Neo4j**, using each database according to the type of information and analysis it is best suited for.

The project also includes data visualisation, graph-based user analysis and a simple recommendation system.

## 🏗️ Hybrid Database Architecture

### MySQL

MySQL is used to store structured and relational information.

The relational model contains three main entities:

- **Users** — reviewer ID and name
- **Products** — product identifier and category
- **Reviews** — rating, date and relationships between users and products

Primary and foreign keys are used to maintain referential integrity and avoid unnecessary data duplication.

### MongoDB

MongoDB stores the less structured information associated with each review:

- Full review text
- Review summary
- Helpfulness information

Each MongoDB document is linked to its corresponding relational review through a `review_id`, allowing structured and unstructured information to be combined when required.

This hybrid architecture separates relational data from textual content while maintaining a connection between both databases.

## 📦 Dataset

The project uses four Amazon Reviews datasets:

- `Digital_Music_5.json`
- `Musical_Instruments_5.json`
- `Toys_and_Games_5.json`
- `Video_Games_5.json`

The datasets are **not included in this repository due to their size**.

To run the project, download the required datasets and place the JSON files in the **root directory of the project**, together with the Python scripts.

## 📥 Data Pipeline

The project includes a Python pipeline to load the Amazon Reviews datasets into the database system.

The process:

1. Reads the JSON review datasets line by line
2. Extracts users, products and structured review information
3. Stores relational data in MySQL
4. Stores textual review information in MongoDB
5. Links both representations through the generated review identifier

Reading the datasets line by line avoids loading the entire dataset into memory.

The system also supports the insertion of additional Amazon Reviews datasets while preserving the existing database structure.

## 📊 Data Analysis and Visualisation

An interactive terminal menu allows different analyses to be performed using the information stored in MySQL and MongoDB.

Implemented analyses and visualisations include:

- Evolution of the number of reviews over time
- Product popularity based on number of reviews
- Distribution of ratings
- Evolution of reviews by product category
- Distribution of reviews per user
- Word clouds generated from review summaries
- Average product rating by category

Users can analyse all available data or filter the results by product category or individual product.

The project also explores the data through **Tableau visualisations**.

## 🕸️ Graph Analysis with Neo4j

Relational data from MySQL is transformed into several graph structures in Neo4j to analyse relationships between users, products and categories.

### User Similarity Graph

The users with the highest number of reviews are selected and their similarity is calculated using the **Pearson correlation coefficient**, considering products reviewed by both users.

The resulting Neo4j graph represents:

- `User` nodes
- `SIMILAR` relationships
- Pearson similarity as a relationship property

This makes it possible to analyse connections between users with similar rating behaviour.

### User-Product Graph

A bipartite graph connects users with the products they have reviewed.

The `REVIEW` relationships contain information such as:

- Rating
- Review timestamp

### User-Category Graph

Users who have reviewed products from several categories are connected to category nodes through `CONSUME` relationships.

Each relationship stores the number of reviews made by that user in the corresponding category.

### Shared Product Analysis

The project also identifies popular products and creates relationships between users who have reviewed products in common, allowing shared consumption patterns to be explored.

## 🎯 Recommendation System

A simple recommendation system was implemented using product popularity.

Given a user and a product category, the system:

1. Identifies the products already reviewed by the user
2. Calculates the most popular products in the selected category
3. Removes products already reviewed by the user
4. Returns the **10 most popular unseen products**

The project also considers how this approach could be extended towards **collaborative filtering**, using similarity between users to generate more personalised recommendations.

## 🛠️ Technologies

- Python
- MySQL
- MongoDB
- Neo4j
- SQL
- Cypher
- PyMySQL
- PyMongo
- Matplotlib
- WordCloud
- Tableau

## 📂 Project Structure

```text
amazon-reviews-data-platform/
│
├── load_data.py
├── inserta_dataset.py
├── menu_visualizacion.py
├── neo4JProyecto.py
├── apartado_cinco.py
├── configuracion.py
│
├── report/
│   ├── project-report.pdf
│   └── project-poster.pdf
│
└── README.md
```

## 💡 Key Concepts

This project combines several data management approaches within a single system:

- Relational database design
- SQL queries and joins
- Document-oriented databases
- Hybrid database architectures
- Data ingestion and ETL
- Graph databases
- Graph modelling
- Pearson similarity
- Data visualisation
- Recommendation systems

## 📄 Project Documentation

A detailed explanation of the database design, implementation and analysis is available in the [project report](report/project-report.pdf).

A visual summary of the project is also available in the [project poster](report/project-poster.pdf).

## 👩‍💻 Authors

**Míriam Mingo Revuelta**  
**Ángela Porres Cobb**

Mathematical Engineering and Artificial Intelligence  
Universidad Pontificia Comillas – ICAI
