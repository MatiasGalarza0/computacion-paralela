<<<<<<< HEAD
import mysql.connector

def conectar_mysql():
    conexion = mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="",
        database="baseproyecto"
    )
    return conexion

if __name__ == "__main__":
    try:
        conexion = conectar_mysql()
        if conexion.is_connected():
            print("Conexion exitosa a la base de datos MySQL")
            print("BASE DE DATOS baseproyecto")
            conexion.close()
    except mysql.connector.Error as error:
        print(f"Error al conectar a la base de datos: {error}")
=======
import mysql.connector

def connector_mysql():

    conexion = mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="",
        database="baseproyecto"
    )
    return conexion

if __name__ == "__main__":
    try:
        conexion = connector_mysql()
        if conexion.is_connected():
            print("Conexion exitosa a la base de datos MYSQL")
            print("BASE DE DATOS proyecto")
            conexion.close()
    except mysql.connector.Error as error:
        print(f"Error al conectar a la vase de datos: {error}")

>>>>>>> 0c3a6d226750c2e9d5a77af3fe1c367bdb38622a
