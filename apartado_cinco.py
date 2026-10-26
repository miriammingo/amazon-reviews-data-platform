# Ángela Porres Cobb y Míriam Mingo Revuelta

import pymysql
import configuracion

def conectar_mysql():
    return pymysql.connect(
        host=configuracion.MYSQL_HOST,
        user=configuracion.MYSQL_USER,
        password=configuracion.MYSQL_PASSWORD,
        database=configuracion.MYSQL_DATABASE
    )

def recomendar_articulos(usuario_id, categoria):
    conn = conectar_mysql()
    cursor = conn.cursor()

    # Comprobamos si el usuario introducido existe 
    cursor.execute("""
        SELECT 1 FROM usuarios WHERE reviewerID = %s
    """, (usuario_id,))

    if cursor.fetchone() is None:
        print(f"El usuario '{usuario_id}' no existe.")
        cursor.close()
        conn.close()
        return
    
    # Comprobamos si la categoría existe
    cursor.execute("""
        SELECT 1 FROM productos WHERE categoria = %s LIMIT 1
    """, (categoria,))

    if cursor.fetchone() is None:
        print(f"La categoría '{categoria}' no existe.")
        cursor.close()
        conn.close()
        return

    # Artículos que ya ha consumido el usuario
    cursor.execute("""
        SELECT r.asin
        FROM reviews r
        JOIN productos p ON r.asin = p.asin
        WHERE r.reviewerID = %s AND p.categoria = %s
    """, (usuario_id, categoria))

    consumidos = set([fila[0] for fila in cursor.fetchall()])

    # Artículos más populares de esa categoría
    cursor.execute("""
        SELECT r.asin, COUNT(*) as total
        FROM reviews r
        JOIN productos p ON r.asin = p.asin
        WHERE p.categoria = %s
        GROUP BY r.asin
        ORDER BY total DESC
    """, (categoria,))

    resultados = cursor.fetchall()

    recomendaciones = []
    i = 0

    while i < len(resultados) and len(recomendaciones) < 10:
        asin, total = resultados[i]

        if asin not in consumidos:
            recomendaciones.append((asin, total))

        i += 1

    cursor.close()
    conn.close()

    print(f"\nRecomendaciones para usuario {usuario_id} en categoría '{categoria}':\n")
    for asin, total in recomendaciones:
        print(f"Artículo: {asin} | Nº reviews: {total}")



if __name__ == "__main__":
    user = input("ID usuario: ")
    cat = input("Categoría: ")
    recomendar_articulos(user, cat)