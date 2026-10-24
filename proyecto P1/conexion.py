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

