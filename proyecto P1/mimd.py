import csv
import threading
import time

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

with open('dataset_indicadores.csv','r',encoding="utf-8-sig", newline="") as archivo:
    lector = csv.reader(archivo)
    next(lector) #saltar la primera fila (encabezado)
    
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
print("Numero de elementos cargados en el dataset: ",len(id))

glucosa_mmol_L = [None] * len(id)
colesterol_mmol_L = [None] * len(id)
trigliceridos_mmol_L = [None] * len(id)

def convertir_glucosa(inicio, fin):
    for i in range(inicio, fin):
        glucosa_mmol_L[i] = round(glucosa_mg_dL[i] / 18.0, 4)

def convertir_colesterol(inicio, fin):
    for i in range(inicio, fin):
        colesterol_mmol_L[i] = round(colesterol_mg_dL[i] / 38.67, 4)

def convertir_trigliceridos(inicio, fin):
    for i in range(inicio, fin):
        trigliceridos_mmol_L[i] = round(trigliceridos_mg_dL[i] / 88.57, 4)

parte = len(id) // 3

h1 = threading.Thread(target=convertir_glucosa, args=(0, parte))
h2 = threading.Thread(target=convertir_colesterol, args=(parte, parte * 2))
h3 = threading.Thread(target=convertir_trigliceridos, args=(parte * 2, len(id)))

h1.start()
h2.start()
h3.start()

h1.join()
h2.join()
h3.join()

print("BLOQUE 1 - GLUCOSA")
for i in range(min(5, parte)):
    print(id[i], glucosa_mmol_L[i])

print("BLOQUE 2 - COLESTEROL")
for i in range(parte, min(parte + 5, parte * 2)):
    print(id[i], colesterol_mmol_L[i])

print("BLOQUE 3 - TRIGLICERIDOS")
for i in range(parte * 2, min(parte * 2 + 5, len(id))):
    print(id[i], trigliceridos_mmol_L[i])

conexion = None
cursor = None

try:
    conexion = conectar_mysql()
    cursor = conexion.cursor()

    print("Conexion exitosa a la base de datos MYSQL")

    sql_original = """
        INSERT INTO registros (id,nombre,apellido,edad,genero,glucosa_mg_dL,colesterol_mg_dL,trigliceridos_mg_dL)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            glucosa_mg_dL = VALUES(glucosa_mg_dL),
            colesterol_mg_dL = VALUES(colesterol_mg_dL),
            trigliceridos_mg_dL = VALUES(trigliceridos_mg_dL)
    """

    sql_resultado = """
        INSERT INTO resultados_mimd(id_mimd, glucosa_mmol_L, colesterol_mmol_L, trigliceridos_mmol_L)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            glucosa_mmol_L = VALUES(glucosa_mmol_L),
            colesterol_mmol_L = VALUES(colesterol_mmol_L),
            trigliceridos_mmol_L = VALUES(trigliceridos_mmol_L)
    """

    for i in range(len(id)):
        cursor.execute(sql_original, (
            id[i],nombre[i],apellido[i],edad[i],
            genero[i],glucosa_mg_dL[i],
            colesterol_mg_dL[i],trigliceridos_mg_dL[i]
        ))

        cursor.execute(sql_resultado, (id[i],
            glucosa_mmol_L[i],
            colesterol_mmol_L[i],
            trigliceridos_mmol_L[i]
        ))

    conexion.commit()

    print("\nDATOS GUARDADOS CORRECTAMENTE\n")
    print("\nREGISTRIS GUARDADOS ",len(id))

except mysql.connector.Error as error:
    if conexion is not None:
        conexion.rollback()
    print(f"Error al guardar los datos en la base de datos: {error}")

finally:
    if cursor is not None:
        cursor.close()
    if conexion is not None and conexion.is_connected():
        conexion.close()

    




