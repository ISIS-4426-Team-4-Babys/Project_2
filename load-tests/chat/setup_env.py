from dotenv import load_dotenv, set_key
import requests
import os


load_dotenv()


BASE_URL =os.getenv("BASE_URL")

ADMIN_NAME = "Manuel Felipe Porras"
ADMIN_EMAIL = "mf.porras@uniandes.edu.co"
ADMIN_PASSWORD = "Porras123"

PROFESSOR_NAME = "Manuela Pacheco Malagon"
PROFESSOR_EMAIL = "m.pachecom2@uniandes.edu.co"
PROFESSOR_PASSWORD = "Manuela123"


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
    print(f"[✓] Professor created: {professor_id}")
    return professor_id

def create_course(token, professor_id):
    payload = {
            "name": "Desarrollo de Soluciones Cloud",
            "code": "ISIS-4116",
            "department": "Ingeniería de Sistemas y Computación",
            "description": "Curso en el cual se enseñan las ventajas y desventajas de la nube",
            "taught_by": f"{professor_id}"
        }
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/courses", json = payload, headers = headers)
    response.raise_for_status()
    course_id = response.json()["id"]
    print(f"[✓] Course created: {course_id}")
    return course_id

def create_agent(token, course_id):
    payload = {
            "name": "Agente Pruebas de Carga",
            "description": "Agente de prueba para las pruebas de carga",
            "is_working": True,
            "system_prompt": "Eres un agente de prueba que responde preguntas del documento",
            "model": "gpt-5",
            "language": "es",
            "retrieval_k": 5,
            "associated_course": course_id
        }
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/agents", json = payload, headers = headers)
    response.raise_for_status()
    agent_id = response.json()["id"]
    append_env_var("AGENT_ID", agent_id)
    print(f"[✓] Agent created: {agent_id}")
    return agent_id

def load_resource(token, agent_id):
    headers = {"Authorization": f"Bearer {token}"}
    
    with open("data/dummy_document.pdf", "rb") as f:
        files = {"file": ("dummy_document.pdf", f, "application/pdf")}
        data = {"name": "Dummy Resource", "consumed_by": f"{agent_id}", "total_docs": "1"}
        requests.post("/resources", data = data, files = files, headers = headers)  
    print(f"[✓] Resource created and loaded to: {agent_id}")

if __name__ == "__main__":

    print("Running setup...")
    register_admin()
    token = login_admin()
    professor_id = create_professor(token)
    course_id = create_course(token, professor_id)
    agent_id = create_agent(token, course_id)
    load_resource(token, agent_id)
    print("\nSetup complete. Values stored in .env")