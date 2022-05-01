from locust import HttpUser, task, between
import json
import uuid
import sys

class WebsiteUser(HttpUser):
    wait_time = between(0.3, 5)

    @task(1)
    def send_tx(self):
        message = {
            "header": {
                "type": "write",
                "ttl": -1,
                "paths": [],
                "source_chain_id": "",
                "target_chain_id": "",
                "auth": {
                    "app_id": "0",
                    "app_info": ""
                },
                "uuid": str(uuid.uuid1()),
            },
            "body": {
                "key": 'test_key',
                "value": 'test_value'
            }
        }
        params = 'tx=0x' + json.dumps(message).encode('utf-8').hex()
        with self.client.post("/broadcast_tx_commit?", params=params, catch_response=True, name="send_normal_tx") as response:
            res = json.loads(response.text)
            if res['result']['deliver_tx']['code'] == 0:
                response.success()
            else:
                response.failure("fail!")

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
    keep_time = num // step + 10
    os.system(
        f"locust -f testokeanosSingleW.py --csv=singleW{num} --csv-full-history --headless -u{num} -r{step} -t{keep_time}s --host=http://localhost:2663")
