from locust import HttpUser, task, constant
from dotenv import load_dotenv
import logging
import os


logging.basicConfig(level = logging.INFO, format = "%(asctime)s [%(levelname)s] %(message)s")


load_dotenv()

AGENT_ID = os.getenv("AGENT_ID")

class ChatUser(HttpUser):

    wait_time = constant(10)
    current_requests = 0
    max_requests = 20

    @task
    def ask_agent(self):

        if self.current_requests >= self.max_requests:
            logging.info(f"Test ran {self.max_requests} times. Stopping")
            self.environment.runner.quit()  
            return

        headers = {
            "Host": f"agent_{AGENT_ID}",
            "Content-Type": "application/json"
        }

        chat_payload = {
            "question": "Considerando la complejidad de la nómina de Kluuvin Apteekki y la preocupación de Pia por perder el control y la seguridad de sus datos, ¿de qué manera un sistema de contabilidad en la nube (AIS) de tipo SaaS público podría simultáneamente solucionar su problema de carga administrativa y agravar sus mayores temores sobre la externalización y la tecnología?"
        }

        with self.client.post(f"/ask", json = chat_payload, headers = headers, catch_response = True) as resp:

            if resp.status_code in (200, 201):
                resp.success()
                logging.info(f"Interaction with chat completed successfully")
            else:
                resp.failure(f"Error asking agent: {resp.status_code}")
        
        self.current_requests += 1


