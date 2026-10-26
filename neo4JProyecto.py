# Ángela Porres Cobb y Míriam Mingo Revuelta

import pymysql
from neo4j import GraphDatabase
import random
import math
from collections import defaultdict
import configuracion

n_usuarios_con_mas_reviews = 30
n_usuarios_ordenados = 400

def conectar_mysql():
    return pymysql.connect(
        host=configuracion.MYSQL_HOST,
        user=configuracion.MYSQL_USER,
        password=configuracion.MYSQL_PASSWORD,
        database=configuracion.MYSQL_DATABASE
    )

def conectar_neo4j():
    return GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "........"))


def limpiar_neo4j(driver):
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")


# Formula de Pearson
def media(valores):
    return sum(valores) / len(valores) if valores else 0

def pearson(r1, r2):
    comunes = set(r1.keys()) & set(r2.keys())  # Articulos en común (Iuv)
    if not comunes:
        return None
    
    # Medias
    m1 = media(r1.values())  
    m2 = media(r2.values())

    numerador = sum((r1[i]-m1)*(r2[i]-m2) for i in comunes)
    den1 = math.sqrt(sum((r1[i]-m1)**2 for i in comunes))
    den2 = math.sqrt(sum((r2[i]-m2)**2 for i in comunes))

    if den1 * den2 == 0:
        return 0

    return numerador / (den1 * den2)

def similitud_usuarios():

    conn = conectar_mysql()
    cursor = conn.cursor()

    # 30 usuarios con más reviews 
    cursor.execute("""
    SELECT reviewerID, COUNT(*) 
    FROM reviews
    GROUP BY reviewerID
    ORDER BY COUNT(*) DESC
    LIMIT %s """, 
    (n_usuarios_con_mas_reviews,))

    usuarios = [u[0] for u in cursor.fetchall()]  # Guardamos solo los id -> (id, count)

    # Obtener valoraciones
    ratings = defaultdict(dict)  

    # Leemos todas las valoraciones de la tabla reviews
    cursor.execute("""
        SELECT reviewerID, asin, overall
        FROM reviews
    """)

    # Las guardamos en un diccionario
    for user, asin, nota in cursor.fetchall():
        if user in usuarios:
            ratings[user][asin] = nota

    driver = conectar_neo4j()
    limpiar_neo4j(driver)

    with driver.session() as session:

        for i in range(len(usuarios)):
            for j in range(i+1, len(usuarios)):     
                u1, u2 = usuarios[i], usuarios[j]

                similitud = pearson(ratings[u1], ratings[u2])

                if similitud is not None:
                    session.run("""
                        MERGE (a:User {id:$u1})
                        MERGE (b:User {id:$u2})
                        MERGE (a)-[r:SIMILAR]-(b)
                        SET r.valor=$sim
                    """, u1=u1, u2=u2, sim=similitud)

    # Usuario con más conexiones
    with driver.session() as session:
        result = session.run("""
            MATCH (u:User)-[:SIMILAR]-()
            RETURN u.id, COUNT(*) as grado
            ORDER BY grado DESC LIMIT 1
        """).single()  

        if result:
            print("Usuario con más vecinos:", result["u.id"], "con", result["grado"], "vecinos")
        else:
            print("No se encontraron similitudes entre usuarios.")
    
    cursor.close()
    conn.close()
    driver.close()


def usuarios_articulos():
    categoria = input("Tipo de artículo: ")
    n = int(input("Número de artículos: "))

    conn = conectar_mysql()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT asin
        FROM productos
        WHERE categoria=%s
    """, (categoria,))

    # Guardamos todos los productos de la categoria elegida
    asins = [a[0] for a in cursor.fetchall()]
    # Elegimos una muestra aleatoria de n artículos
    seleccion = random.sample(asins, min(n, len(asins)))

    cursor.execute("""
        SELECT reviewerID, asin, overall, unixReviewTime
        FROM reviews
    """)

    driver = conectar_neo4j()
    limpiar_neo4j(driver)

    with driver.session() as session:
        for user, asin, nota, tiempo in cursor.fetchall():
            if asin in seleccion:
                session.run("""
                    MERGE (u:User {id:$u})
                    MERGE (a:Articulo {id:$a})
                    MERGE (u)-[r:REVIEW]->(a)
                    SET r.nota=$nota, r.tiempo=$tiempo
                """, u=user, a=asin, nota=nota, tiempo=tiempo)

    print("Carga completada en Neo4J")
    cursor.close()
    conn.close()
    driver.close()


def usuarios_multicategoria():
    conn = conectar_mysql()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT reviewerID
        FROM usuarios
        ORDER BY reviewerName
        LIMIT %s
    """, (n_usuarios_ordenados,))

    users = [u[0] for u in cursor.fetchall()]

    # Obtenemos para cada usuario y categoría cuántas reviews ha hecho
    datos = defaultdict(dict)

    for user in users:
        cursor.execute("""
            SELECT p.categoria, COUNT(*)
            FROM reviews r
            JOIN productos p ON r.asin = p.asin
            WHERE r.reviewerID = %s
            GROUP BY p.categoria
        """, (user,))

        for categoria, total in cursor.fetchall():
            datos[user][categoria] = total

    driver = conectar_neo4j()
    limpiar_neo4j(driver)

    with driver.session() as session:
        for user, categorias in datos.items():
            if len(categorias) > 1:
                for categoria, total in categorias.items():
                    session.run("""
                        MERGE (u:User {id:$u})
                        MERGE (c:Categoria {nombre:$c})
                        MERGE (u)-[r:CONSUME]->(c)
                        SET r.total=$t
                    """, u=user, c=categoria, t=total)

    print("Carga completada en Neo4J")
    cursor.close()
    conn.close()
    driver.close()

def articulos_populares():
    conn = conectar_mysql()
    cursor = conn.cursor()

    # Buscamos los 5 artículos más populares que tengan menos de 40 reviews
    cursor.execute("""
        SELECT asin, COUNT(*) as total
        FROM reviews
        GROUP BY asin
        HAVING total < 40
        ORDER BY total DESC
        LIMIT 5
    """)

    articulos = [a[0] for a in cursor.fetchall()]

    # Leemos todas las reviews
    cursor.execute("""
        SELECT reviewerID, asin
        FROM reviews
    """)

    datos = cursor.fetchall()

    driver = conectar_neo4j()
    limpiar_neo4j(driver)

    usuarios_art = defaultdict(set)

    # Solo los artículos elegidos
    for user, asin in datos:
        if asin in articulos:
            usuarios_art[user].add(asin)

    with driver.session() as session:

        # Creamos los nodos
        for user, arts in usuarios_art.items():
            session.run("MERGE (u:User {id:$u})", u=user)
            for a in arts:
                session.run("MERGE (a:Articulo {id:$a})", a=a)
                session.run("""
                    MATCH (u:User {id:$u}), (a:Articulo {id:$a})
                    MERGE (u)-[:REVIEW]->(a)
                """, u=user, a=a)

        # Enlaces entre usuarios
        users = list(usuarios_art.keys())

        for i in range(len(users)):
            for j in range(i+1, len(users)):
                # Calculamis cuantos artículos han puntuado en común
                comunes = usuarios_art[users[i]] & usuarios_art[users[j]]
                if comunes:
                    session.run("""
                        MATCH (a:User {id:$u1}), (b:User {id:$u2})
                        MERGE (a)-[r:COMPARTE]-(b)
                        SET r.total=$t
                    """, u1=users[i], u2=users[j], t=len(comunes))

    print("Carga completada en Neo4J")
    cursor.close()
    conn.close()
    driver.close()

def menu():
    seguir = True
    while seguir:
        print("\n      MENÚ NEO4J")
        print("1. Similitud usuarios")
        print("2. Usuarios y artículos")
        print("3. Usuarios multicategoría")
        print("4. Artículos populares")
        print("0. Salir")

        op = input("Opción: ")

        if op == "1":
            similitud_usuarios()
        elif op == "2":
            usuarios_articulos()
        elif op == "3":
            usuarios_multicategoria()
        elif op == "4":
            articulos_populares()
        elif op == "0":
            seguir = False
        else:
            print("Opción no válida")

if __name__ == "__main__":
    menu()