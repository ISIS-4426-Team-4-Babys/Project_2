from locust import HttpUser, task, constant
from rabbitmq import RabbitMQ
import threading
import logging
import asyncio
import random
import time
import json
import csv
import os


logging.basicConfig(level = logging.INFO, format = "%(asctime)s [%(levelname)s] %(message)s")
agent_start_times = {}


RESULTS_FILE = "deploy_start_times.csv"


if not os.path.exists(RESULTS_FILE):
    with open(RESULTS_FILE, mode = "w", newline = "") as f:
        writer = csv.writer(f)
        writer.writerow(["agent_id", "start_time"])


class FullLoadUser(HttpUser):

    wait_time = constant(10)

    admin_name = "Nicolas Rozo Fajardo"
    admin_email = "n.rozo@uniandes.edu.co"
    admin_password = "admin123"
    admin_token = None

    professor_name = "Juan Andres Ariza"
    professor_email = "ja.arizag@uniandes.edu.co"
    professor_password = "Juan123"
    professor_id = None
    course_id = None

    max_requests = 20
    current_requests = 0

    def on_start(self):

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
            logging.info(f"Admin logged successfully")

        
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

        if self.current_requests >= self.max_requests:
            logging.info("Test ran 20 times. Stopping")
            self.environment.runner.quit()  
            return
        
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
                logging.info(f"Agent created successfully")
                if agent_id:
                    agent_start_times[agent_id] = time.time()

                    with open(RESULTS_FILE, mode="a", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow([agent_id, f"{agent_start_times[agent_id]:.2f}"])

                    resp.success()
                else:
                    resp.failure("Cant access to agent_id")
                    return
            else:
                resp.failure(f"Error creating agent: {resp.status_code}")
                return

        with open("dummy_document.pdf", "rb") as f:
            files = {"file": ("dummy_document.pdf", f, "application/pdf")}
            data = {"name": "Dummy Resource", "consumed_by": f"{agent_id}", "total_docs": "1"}
            self.client.post("/resources", data = data, files = files, headers = headers)
            logging.info(f"Resource created successfully")
        
        self.current_requests += 1