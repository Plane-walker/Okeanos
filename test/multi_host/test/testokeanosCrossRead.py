from locust import HttpUser, task, between
import requests
import time
import datetime
import json
import uuid
import sys

source_chain_id = ""
target_chain_id = ""
target_ip = ""

class WebsiteUser(HttpUser):
    wait_time = between(0.3, 5)

    @task(1)
    def query_cross_tx(self):
        cross_uuid = str(uuid.uuid1())
        message = {
            "header": {
                "type": "cross_read",
                "ttl": -1,
                "paths": [],
                "source_chain_id": source_chain_id,
                "target_chain_id": target_chain_id,
                "auth": {
                    "app_id": "0"
                },
                "uuid": str(uuid.uuid1()),
            },
            "body": {
                "key": cross_uuid
            }
        }
        params = 'tx=0x' + json.dumps(message).encode('utf-8').hex()
        with self.client.post("/abci_query?", params=params, catch_response=True, name="query_cross_tx") as response:
            message = {
                "header": {
                    "type": "read",
                    "ttl": -1,
                    "paths": [],
                    "source_chain_id": "",
                    "target_chain_id": "",
                    "auth": {
                        "app_id": "0"
                    },
                    "uuid": str(uuid.uuid1()),
                },
                "body": {
                    "key": f"response_for_query_{cross_uuid}"
                }
            }
            params = 'data=0x' + json.dumps(message).encode('utf-8').hex()
            start_time = datetime.datetime.now()
            timeout = 15
            while True:
                res = requests.get(
                    f"http://localhost:2663/abci_query", params=params)
                if json.loads(res.text)['result']['response']['code'] == 0:
                    response.success()
                    break
                if (datetime.datetime.now() - start_time).seconds > timeout:
                    response.failure("fail!")
                    break
                time.sleep(1)

if __name__ == "__main__":
    import os
    num = int(sys.argv[1])
    if num < 20:
        step = 2
    elif num > 20 and num < 130:
        step = 10
    elif num > 130 and num < 520:
        step = 30
    elif num > 520 and num < 1030:
        step = 50
    else:
        step = 100
    keep_time = num // step + 20
    os.system(
        f"locust -f testokeanosCrossRead.py --csv=CrossRead{num} --csv-full-history --headless -u{num} -r{step} -t{keep_time}s --host=http://localhost:2663")
