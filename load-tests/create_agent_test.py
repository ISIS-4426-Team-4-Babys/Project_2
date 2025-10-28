from locust import HttpUser, task, constant
from rabbitmq import RabbitMQ
import threading
import logging
import asyncio
import random
import time
import json


logging.basicConfig(level = logging.INFO, format = "%(asctime)s [%(levelname)s] %(message)s")


agent_start_times = {}


async def on_deploy_message(message):
    try:
        body = message.body.decode().strip()
        data = json.loads(body)
        agent_id = data.get("agent_id")
        logging.info(f"Received message = {agent_id}")

        if  agent_id in agent_start_times:
            start_time = agent_start_times.pop(agent_id)
            total_time = (time.time() - start_time) * 1000  
            logging.info(f"Agent {agent_id} deployed in {total_time:.2f} ms")

    except Exception as e:
        logging.error(f"Error processing message: {e}")


def start_rabbitmq_listener(env):
    async def runner():
        client = RabbitMQ()
        await client.connect()
        await client.consume("deploy", on_deploy_message)

    thread = threading.Thread(target = lambda: asyncio.run(runner()), daemon = True)
    thread.start() 
    return thread


class FullLoadUser(HttpUser):

    wait_time = constant(120)

    admin_name = "Nicolas Rozo Fajardo"
    admin_email = "n.rozo@uniandes.edu.co"
    admin_password = "admin123"
    admin_token = None

    professor_name = "Juan Andres Ariza"
    professor_email = "ja.arizag@uniandes.edu.co"
    professor_password = "Juan123"
    professor_id = None
    course_id = None

    def on_start(self):

        if not hasattr(self.environment, "rabbit_thread"):
            self.environment.rabbit_thread = start_rabbitmq_listener(self.environment)
            logging.info("Rabbit MQ Listener Started")

        payload = {
            "name": self.admin_name,
            "email": self.admin_email,
            "role": "admin",
            "password": self.admin_password,
            "profile_image": "https://revistaenraizada.com/wp-content/uploads/2021/08/Tamaulipas.jpg"
        }

        with self.client.post("/auth/register", json = payload, catch_response = True) as resp:
            if resp.status_code not in (200, 201, 400):
                resp.failure(f"Error registering admin: {resp.status_code}")
            logging.info("Admin created successfully")
        
        payload = {
            "email": self.admin_email, 
            "password": self.admin_password
        }

        with self.client.post("/auth/login", json = payload, catch_response = True) as resp:
            if resp.status_code not in (200, 201):
                resp.failure(f"Error login admin: {resp.status_code}")
            self.admin_token = resp.json().get("access_token")
            logging.info(f"Admin logged successfully with token {self.admin_token}")

        
        payload = {
            "name": self.professor_name,
            "email": self.professor_email,
            "password": self.professor_password,
            "role": "professor",
            "profile_image": "https://www.instagram.com/sanguchedemortadela__/p/DBEj19gPnEM/?locale=es_LA" 
        }

        headers = {"Authorization": f"Bearer {self.admin_token}"}
        with self.client.post("/users", json = payload, headers = headers, catch_response = True) as resp:
            if resp.status_code not in (200, 201, 400):
                resp.failure(f"Error registering professor: {resp.status_code}")
            self.professor_id = resp.json().get("id") if resp.status_code != 400 else None
            logging.info(f"Professor created successfully with id {self.professor_id}")


        payload = {
            "name": "Diseño de Pruebas de Carga",
            "code": "ISIS-4115",
            "department": "Ingeniería de Sistemas y Computación",
            "description": "Curso en el cual se enseñan a diseñar, ejecutar y evaluar pruebas de carga a aplicaciones",
            "taught_by": f"{self.professor_id}"
        }

        headers = {"Authorization": f"Bearer {self.admin_token}"}
        with self.client.post("/courses", json = payload, headers = headers, catch_response = True) as resp:
            if resp.status_code not in (200, 201, 400):
                resp.failure(f"Error creating course: {resp.status_code}")
            self.course_id = resp.json().get("id") if resp.status_code != 400 else None
            logging.info(f"Course created successfully with id {self.course_id}")


    @task
    def create_agent_with_resources(self):

        headers = {"Authorization": f"Bearer {self.admin_token}"}

        agent_payload = {
            "name": "Agente Pruebas de Carga",
            "description": "Agente de prueba para las pruebas de carga",
            "is_working": True,
            "system_prompt": "Eres un agente de prueba que responde preguntas del documento",
            "model": "gpt-5",
            "language": "es",
            "retrieval_k": 5,
            "associated_course": self.course_id
        }

        with self.client.post("/agents", json = agent_payload, headers = headers, catch_response = True) as resp:
            if resp.status_code in (200, 201):
                agent_id = resp.json().get("id")
                logging.info(f"Agent created successfully with id {agent_id}")
                if agent_id:
                    agent_start_times[agent_id] = time.time()
                    resp.success()
                else:
                    logging.info("Error creating agent")
                    resp.failure("Cant access to agent_id")
                    return
            else:
                logging.info("Error creating agent")
                resp.failure(f"Error creating agent: {resp.status_code}")
                return

        with open("dummy_document.pdf", "rb") as f:
            files = {"file": ("dummy_document.pdf", f, "application/pdf")}
            data = {"name": "Dummy Resource", "consumed_by": f"{agent_id}", "total_docs": "1"}
            self.client.post("/resources", data = data, files = files, headers = headers)

