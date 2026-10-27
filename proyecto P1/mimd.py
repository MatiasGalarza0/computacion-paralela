import csv
import threading

from conexion import conectar_mysql
import mysql.connector

id = []
nombre = []
apellido = []
edad = []
genero = []
glucosa_mg_dL = []
colesterol_mg_dL = []
trigliceridos_mg_dL = []

with open("dataset_indicadores.csv", "r", encoding="utf-8-sig", newline="") as archivo:
    lector = csv.reader(archivo)
    next(lector)

    for fila in lector:
        id.append(int(fila[0]))
        nombre.append(fila[1])
        apellido.append(fila[2])
        edad.append(fila[3])
        genero.append(fila[4])
        glucosa_mg_dL.append(float(fila[5]))
        colesterol_mg_dL.append(float(fila[6]))
        trigliceridos_mg_dL.append(float(fila[7]))

print("Dataset cargado correctamente")
print("Numero de elementos cargados: ", len(id))

resultados = [None] * len(id)


def convertir_glucosa(inicio, fin):
    for i in range(inicio, fin):
        valor = round(glucosa_mg_dL[i] / 18.0, 4)
        resultados[i] = ("Glucosa", valor)


def convertir_colesterol(inicio, fin):
    for i in range(inicio, fin):
        valor = round(colesterol_mg_dL[i] / 38.67, 4)
        resultados[i] = ("Colesterol", valor)


def convertir_trigliceridos(inicio, fin):
    for i in range(inicio, fin):
        valor = round(trigliceridos_mg_dL[i] / 88.57, 4)
        resultados[i] = ("Triglicéridos", valor)


parte = len(id) // 3

h1 = threading.Thread(
    target=convertir_glucosa,
    args=(0, parte)
)

h2 = threading.Thread(
    target=convertir_colesterol,
    args=(parte, parte * 2)
)

h3 = threading.Thread(
    target=convertir_trigliceridos,
    args=(parte * 2, len(id))
)

h1.start()
h2.start()
h3.start()

h1.join()
h2.join()
h3.join()

if any(resultado is None for resultado in resultados):
    raise RuntimeError("Hay registros sin calcular. No se guardaron los resultados.")

print("BLOQUE 1 - GLUCOSA")
for i in range(min(5, parte)):
    print(id[i], resultados[i][1])

print("BLOQUE 2 - COLESTEROL")
for i in range(parte, min(parte + 5, parte * 2)):
    print(id[i], resultados[i][1])

print("BLOQUE 3 - TRIGLICERIDOS")
for i in range(parte * 2, min(parte * 2 + 5, len(id))):
    print(id[i], resultados[i][1])

conexion = None
cursor = None

try:
    conexion = conectar_mysql()
    cursor = conexion.cursor()

    print("Conexion exitosa a la base de datos MYSQL")

    sql_original = """
        INSERT INTO registros (
            id, nombre, apellido, edad, genero,
            glucosa_mg_dL, colesterol_mg_dL, trigliceridos_mg_dL
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            glucosa_mg_dL = VALUES(glucosa_mg_dL),
            colesterol_mg_dL = VALUES(colesterol_mg_dL),
            trigliceridos_mg_dL = VALUES(trigliceridos_mg_dL)
    """

    sql_resultado = """
        INSERT INTO resultados_mimd (
            id_mimd, conversion, resultado
        )
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            conversion = VALUES(conversion),
            resultado = VALUES(resultado)
    """

    for i in range(len(id)):
        cursor.execute(sql_original, (
            id[i],
            nombre[i],
            apellido[i],
            edad[i],
            genero[i],
            glucosa_mg_dL[i],
            colesterol_mg_dL[i],
            trigliceridos_mg_dL[i]
        ))

        conversion, valor = resultados[i]

        cursor.execute(sql_resultado, (
            id[i],
            conversion,
            valor
        ))

    conexion.commit()

    print("\nDATOS GUARDADOS CORRECTAMENTE")
    print("REGISTROS GUARDADOS: ", len(id))

except mysql.connector.Error as error:
    if conexion is not None:
        conexion.rollback()

    print(f"Error al guardar los datos: {error}")

finally:
    if cursor is not None:
        cursor.close()

    if conexion is not None and conexion.is_connected():
        conexion.close()
