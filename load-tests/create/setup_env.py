from dotenv import load_dotenv, set_key
import requests
import os


load_dotenv()


BASE_URL =os.getenv("BASE_URL")

ADMIN_NAME = "Nicolas Rozo Fajardo"
ADMIN_EMAIL = "n.rozo@uniandes.edu.co"
ADMIN_PASSWORD = "Admin123"

PROFESSOR_NAME = "Juan Andrés Aríza"
PROFESSOR_EMAIL = "ja.arizag@uniandes.edu.co"
PROFESSOR_PASSWORD = "Juan123"


def append_env_var(key, value):
    set_key(".env", key, str(value))

def register_admin():
    payload = {
            "name": ADMIN_NAME,
            "email": ADMIN_EMAIL,
            "role": "admin",
            "password": ADMIN_PASSWORD,
            "profile_image": "https://revistaenraizada.com/wp-content/uploads/2021/08/Tamaulipas.jpg"
        }

    requests.post(f"{BASE_URL}/auth/register", json = payload)

def login_admin():
    payload = {
            "email": ADMIN_EMAIL, 
            "password": ADMIN_PASSWORD
        }

    response = requests.post(f"{BASE_URL}/auth/login", json = payload)
    response.raise_for_status()
    token = response.json()["access_token"]
    append_env_var("ADMIN_TOKEN", token)
    print("[✓] Admin login successful")
    return token

def create_professor(token):
    payload = {
            "name": PROFESSOR_NAME,
            "email": PROFESSOR_EMAIL,
            "password": PROFESSOR_PASSWORD,
            "role": "professor",
            "profile_image": "https://www.instagram.com/sanguchedemortadela__/p/DBEj19gPnEM/?locale=es_LA" 
        }

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/users", json = payload, headers = headers)
    response.raise_for_status()
    professor_id = response.json()["id"]
    append_env_var("PROFESSOR_ID", professor_id)
    print(f"[✓] Professor created: {professor_id}")
    return professor_id

def create_course(token, professor_id):
    payload = {
            "name": "Diseño de Pruebas de Carga",
            "code": "ISIS-4115",
            "department": "Ingeniería de Sistemas y Computación",
            "description": "Curso en el cual se enseñan a diseñar, ejecutar y evaluar pruebas de carga a aplicaciones",
            "taught_by": f"{professor_id}"
        }
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/courses", json = payload, headers = headers)
    response.raise_for_status()
    course_id = response.json()["id"]
    append_env_var("COURSE_ID", course_id)
    print(f"[✓] Course created: {course_id}")
    return course_id


if __name__ == "__main__":

    print("Running setup...")
    register_admin()
    token = login_admin()
    professor_id = create_professor(token)
    create_course(token, professor_id)
    print("\nSetup complete. Values stored in .env")