from locust import HttpUser, task, constant
from dotenv import load_dotenv
import logging
import time
import csv
import os


logging.basicConfig(level = logging.INFO, format = "%(asctime)s [%(levelname)s] %(message)s")


load_dotenv()


RESULTS_FILE = "deploy_start_times.csv"
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
COURSE_ID = os.getenv("COURSE_ID")


if not os.path.exists(RESULTS_FILE):
    with open(RESULTS_FILE, mode = "w", newline = "") as f:
        writer = csv.writer(f)
        writer.writerow(["agent_id", "start_time"])


agent_start_times = {}


class FullLoadUser(HttpUser):

    wait_time = constant(10)
    current_requests = 0
    max_requests = 20

    @task
    def create_agent_with_resources(self):

        if self.current_requests >= self.max_requests:
            logging.info(f"Test ran {self.max_requests} times. Stopping")
            self.environment.runner.quit()  
            return
        
        headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}

        agent_payload = {
            "name": "Agente Pruebas de Carga",
            "description": "Agente de prueba para las pruebas de carga",
            "is_working": True,
            "system_prompt": "Eres un agente de prueba que responde preguntas del documento",
            "model": "gpt-5",
            "language": "es",
            "retrieval_k": 5,
            "associated_course": COURSE_ID
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


        with open("data/dummy_document.pdf", "rb") as f:
            files = {"file": ("dummy_document.pdf", f, "application/pdf")}
            data = {"name": "Dummy Resource", "consumed_by": f"{agent_id}", "total_docs": "1"}
            self.client.post("/resources", data = data, files = files, headers = headers)
            logging.info(f"Resource created successfully")
        
        self.current_requests += 1