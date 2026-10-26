# Ángela Porres Cobb y Míriam Mingo Revuelta

import json
import pymysql
from pymongo import MongoClient
from datetime import datetime
import configuracion

# MySQL
mysql_conn = pymysql.connect(
    host=configuracion.MYSQL_HOST,
    user=configuracion.MYSQL_USER,
    password=configuracion.MYSQL_PASSWORD
)
cursor = mysql_conn.cursor()

# MongoDB
mongo_client = MongoClient(configuracion.MONGO_URI)
mongo_db = mongo_client[configuracion.MONGO_DATABASE]
mongo_collection = mongo_db[configuracion.MONGO_COLLECTION]

def crear_bbdd():
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {configuracion.MYSQL_DATABASE}")
    cursor.execute(f"USE {configuracion.MYSQL_DATABASE}")

def crear_tablas():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios(
        reviewerID VARCHAR(50) PRIMARY KEY,
        reviewerName VARCHAR(255)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS productos(
        asin VARCHAR(50) PRIMARY KEY,
        categoria VARCHAR(50)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews(
        id_review INT AUTO_INCREMENT PRIMARY KEY,
        reviewerID VARCHAR(50),
        asin VARCHAR(50),
        overall FLOAT,
        unixReviewTime BIGINT,
        reviewTime DATE,
        FOREIGN KEY (reviewerID) REFERENCES usuarios(reviewerID),
        FOREIGN KEY (asin) REFERENCES productos(asin)
    )
    """)

def cargar_datos():
    for categoria, ruta in configuracion.DATASETS.items():
        usuarios_sql = []
        productos_sql = []
        reviews_sql = []
        mongo_docs = []

        with open(ruta, "r", encoding="utf-8") as f:
            for linea in f:  # Recorremos cada dataset linea a linea
                
                review = json.loads(linea)  # Convertimos cada string a un dict para extraer la info
                reviewerID = review["reviewerID"]
                reviewerName = review.get("reviewerName", "")
                asin = review["asin"]
                overall = review["overall"]
                unixTime = review["unixReviewTime"]
                fecha = datetime.strptime(review["reviewTime"], "%m %d, %Y")

                usuarios_sql.append((reviewerID, reviewerName))
                productos_sql.append((asin, categoria))
                reviews_sql.append((reviewerID, asin, overall, unixTime, fecha))
             
                mongo_docs.append({
                    "review_id": None,  # Lo actualizaremos luego
                    "reviewText": review.get("reviewText", ""),
                    "summary": review.get("summary", ""),
                    "helpful": review.get("helpful", [])
                })

        # Hacemos un insert masivo de usuarios y productos para que vaya más rápido (ignorando duplicados)
        cursor.executemany("""INSERT IGNORE INTO usuarios (reviewerID, reviewerName) 
                            VALUES (%s, %s)""", usuarios_sql)
        cursor.executemany("""INSERT IGNORE INTO productos (asin, categoria) 
                            VALUES (%s, %s)""", productos_sql)

        # Hacemos también un insert masivo de reviews
        cursor.executemany("""INSERT INTO reviews (reviewerID, asin, overall, unixReviewTime, reviewTime)
                              VALUES (%s, %s, %s, %s, %s)""", reviews_sql)
        
        mysql_conn.commit()

        # Obtenemos los ids de las reviews insertadas para usarlos en Mongo (así conectamos SQL con Mongo)
        cursor.execute("""SELECT id_review 
                       FROM reviews 
                       ORDER BY id_review DESC 
                       LIMIT %s
                       """, (len(reviews_sql),))
        
        ids = [fila[0] for fila in cursor.fetchall()]

        # Asignamos cada id correcto a cada documento de Mongo
        for i, doc in enumerate(reversed(mongo_docs)):  # (reversed porque con MySQL lo devolvimos en orden DESC)
            doc["review_id"] = ids[i]

        # AHora hacemos un insert masivo en Mongo
        if mongo_docs:
            mongo_collection.insert_many(mongo_docs)

if __name__ == "__main__":
    crear_bbdd()
    crear_tablas()
    cargar_datos()
    print("Datos cargados correctamente")