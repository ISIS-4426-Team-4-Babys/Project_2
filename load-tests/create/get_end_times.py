from rabbitmq import RabbitMQ
from dotenv import load_dotenv
import logging
import asyncio
import json
import csv
import os


load_dotenv()


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
rabbitmq = RabbitMQ()


RESULTS_FILE = "deploy_end_times.csv"


if not os.path.exists(RESULTS_FILE):
    with open(RESULTS_FILE, mode = "w", newline = "") as f:
        writer = csv.writer(f)
        writer.writerow(["agent_id", "end_time"])


async def callback(message):
    try:
        decoded_message = message.body.decode().strip()
        logging.info(f"Message received with content = {decoded_message}")

        payload = json.loads(decoded_message)
        agent_id = payload.get("agent_id")
        end_time = payload.get("end_time")

        with open(RESULTS_FILE, mode = "a", newline = "") as f:
                writer = csv.writer(f)
                writer.writerow([agent_id, f"{end_time:.2f}"])
    except Exception as e:
        logging.error(f"Error processing message: {e}")


async def main():
    await rabbitmq.consume("create_agent_test", callback)


if __name__ == "__main__":
    asyncio.run(main())



