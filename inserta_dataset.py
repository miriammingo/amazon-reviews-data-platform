# Ángela Porres Cobb y Míriam Mingo Revuelta

import json
from datetime import datetime

import pymysql
from pymongo import MongoClient

import configuracion


def conectar_mysql():
    return pymysql.connect(
        host=configuracion.MYSQL_HOST,
        user=configuracion.MYSQL_USER,
        password=configuracion.MYSQL_PASSWORD,
        database=configuracion.MYSQL_DATABASE
    )


def conectar_mongo():
    client = MongoClient(configuracion.MONGO_URI)
    db = client[configuracion.MONGO_DATABASE]
    return client, db[configuracion.MONGO_COLLECTION]


def insertar_nuevo_dataset(ruta, categoria):
    conn = conectar_mysql()
    cursor = conn.cursor()
    mongo_client, mongo_collection = conectar_mongo()

    usuarios_sql = []
    productos_sql = []
    reviews_sql = []
    mongo_docs = []

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            for linea in f:
                # Convertimos cada linea en un diccionario
                review = json.loads(linea)

                reviewerID = review["reviewerID"]
                reviewerName = review.get("reviewerName", "")  # En caso de que no exista, devuelve vacio 
                asin = review["asin"]
                overall = review["overall"]
                unix_time = review["unixReviewTime"]
                fecha = datetime.strptime(review["reviewTime"], "%m %d, %Y")

                usuarios_sql.append((reviewerID, reviewerName))
                productos_sql.append((asin, categoria))
                reviews_sql.append((reviewerID, asin, overall, unix_time, fecha))

                mongo_docs.append({
                    "review_id": None,  # Todaía no lo sabemos
                    "reviewText": review.get("reviewText", ""),
                    "summary": review.get("summary", ""),
                    "helpful": review.get("helpful", [])
                })

        # Inserciones en MySQL
        # En caso de que un usuario ya exista, lo ignoramos
        cursor.executemany("""
            INSERT IGNORE INTO usuarios (reviewerID, reviewerName)
            VALUES (%s, %s)
        """, usuarios_sql)

        cursor.executemany("""
            INSERT IGNORE INTO productos (asin, categoria)
            VALUES (%s, %s)
        """, productos_sql)

         
        cursor.executemany("""
            INSERT INTO reviews (reviewerID, asin, overall, unixReviewTime, reviewTime)
            VALUES (%s, %s, %s, %s, %s)
        """, reviews_sql)

        conn.commit()

        # Obtenemos IDs insertados
        cursor.execute("""
            SELECT id_review
            FROM reviews
            ORDER BY id_review DESC
            LIMIT %s
        """, (len(reviews_sql),))

        ids_reviews = [fila[0] for fila in cursor.fetchall()]

        # Asignamos estos IDs a Mongo
        for i, doc in enumerate(reversed(mongo_docs)):
            doc["review_id"] = ids_reviews[i]

        # Insertamos en Mongo
        if len(mongo_docs) > 0:
            mongo_collection.insert_many(mongo_docs)

        print(f"Dataset '{categoria}' insertado correctamente.")

    except Exception as e:
        print(f"Error durante la inserción: {e}")

    # Cerramos las conexiones
    cursor.close()
    conn.close()
    mongo_client.close()


if __name__ == "__main__":
    insertar_nuevo_dataset(
        configuracion.NUEVO_DATASET_RUTA,
        configuracion.NUEVA_CATEGORIA
    )