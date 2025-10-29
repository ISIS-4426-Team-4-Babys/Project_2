from locust import HttpUser, task
from dotenv import load_dotenv
import logging
import os


logging.basicConfig(level = logging.INFO, format = "%(asctime)s [%(levelname)s] %(message)s")


load_dotenv()


class ChatUser(HttpUser):

    @task
    def ask_agent(self):

        agent_id = os.getenv("AGENT_ID")

        headers = {
            "Host": f"agent_{agent_id}",
            "Content-Type": "application/json"
        }

        chat_payload = {
            "question": "Considerando la complejidad de la nómina de Kluuvin Apteekki y la preocupación de Pia por perder el control y la seguridad de sus datos, ¿de qué manera un sistema de contabilidad en la nube (AIS) de tipo SaaS público podría simultáneamente solucionar su problema de carga administrativa y agravar sus mayores temores sobre la externalización y la tecnología?"
        }

        logging.info(f"Starting interaction with chat")
        with self.client.post(f"/ask", json = chat_payload, headers=headers, catch_response = True) as resp:

            if resp.status_code in (200, 201):
                resp.success()
                logging.info(f"Interaction with chat completed successfully")
            else:
                resp.failure(f"Error creating agent: {resp.status_code}")
        
        self.environment.runner.quit()
        return


