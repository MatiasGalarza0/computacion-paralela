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
    print("Numero de elementos cargados en el dataset: ",len(id))

glucosa_mmol_L = [0.0] *len(glucosa_mg_dL) 
colesterol_mmol_L = [0.0] *len(colesterol_mg_dL)
trigliceridos_mmol_L = [0.0] *len(trigliceridos_mg_dL)

def convertir_glucosa():
    for i in range(len(glucosa_mg_dL)): 
        glucosa_mmol_L[i] = round(glucosa_mg_dL[i]/18,4)

def convertir_colesterol():
    for i in range(len(colesterol_mg_dL)):
        colesterol_mmol_L[i] = round(colesterol_mg_dL[i]/38.67,4)

def convertir_trigliceridos():
    for i in range(len(trigliceridos_mg_dL)):
        trigliceridos_mmol_L[i] = round(trigliceridos_mg_dL[i]/88.57,4)

h1 = threading.Thread(target=convertir_glucosa) 
h2 = threading.Thread(target=convertir_colesterol)
h3 = threading.Thread(target=convertir_trigliceridos)

h1.start() 
h2.start()
h3.start()

h1.join() 
h2.join()
h3.join()

for i in range(len(glucosa_mg_dL)):
    print("\n------------------------------")
    print("REGISTRO: ", id[i])
    print(f"Glucosa:  {glucosa_mmol_L[i]:.4f} mmol/L")
    print(f"Colesterol: , {colesterol_mmol_L[i]:.4f}")
    print(f"Trigliceridos: , {trigliceridos_mmol_L[i]:.4f} ")
    
print("PRIMER REGISTRO:" , id[0])
print("ULTIMO REGISTRO:" , id[-1])
print("TOTAL REGISTROS:" , len(id))

print("\n------------------------------")

conexion = None
cursor = None

try:
    conexion = conectar_mysql() 
    cursor = conexion.cursor() 
    
    print("Conexion exitosa a la base de datos MySQL")
    sql_original = """
        INSERT INTO registros(id, nombre, apellido,edad, genero, glucosa_mg_dL, colesterol_mg_dL, trigliceridos_mg_dL) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            glucosa_mg_dL = VALUES(glucosa_mg_dL),
            colesterol_mg_dL = VALUES(colesterol_mg_dL),
            trigliceridos_mg_dL = VALUES(trigliceridos_mg_dL)
    """

    sql_resultado = """
        INSERT INTO resultados_misd(id_misd, glucosa_mmol_L,colesterol_mmol_L, trigliceridos_mmol_L)
        VALUES(%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
                glucosa_mmol_L = VALUES(glucosa_mmol_L),
                colesterol_mmol_L = VALUES(colesterol_mmol_L),
                trigliceridos_mmol_L = VALUES(trigliceridos_mmol_L)
    """
    
    for i in range(len(glucosa_mg_dL)):
        cursor.execute(sql_original, (id[i], nombre[i], apellido[i], edad[i], genero[i], glucosa_mg_dL[i], colesterol_mg_dL[i], trigliceridos_mg_dL[i]))
        cursor.execute(sql_resultado, (id[i], glucosa_mmol_L[i], colesterol_mmol_L[i], trigliceridos_mmol_L[i]))
        
    conexion.commit() 
    print(" \n DATOS GUARDADOS CORRECTAMENTE")
    print(" \n REGISTROS GUARDADOS", len(id))

except mysql.connector.Error as error:
    if conexion is not None:
        conexion.rollback()
    print(f"Error al guardar los datos en la base de datos:{error}")
    
finally:
    if cursor is not None:
        cursor.close()
    if conexion is not None and conexion.is_connected():
        conexion.close()
    