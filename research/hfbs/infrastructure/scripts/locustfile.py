from locust import HttpUser, task, between
import random

EVENT_ID = 1

class BookingUser(HttpUser):
    wait_time = between(0.5, 2)
    token = None

    def on_start(self):
        # Определяем тип auth по порту
        if "8001" in self.host:
            r = self.client.post("/api/v1/auth/token/",
                data={"username": "loadtest", "password": "loadtest123"})
            if r.status_code == 200:
                self.token = r.json().get("access_token")
        else:
            r = self.client.post("/api/v1/auth/token/",
                json={"username": "loadtest", "password": "loadtest123"})
            if r.status_code == 200:
                self.token = r.json().get("access")

        if self.token:
            self.client.headers["Authorization"] = f"Bearer {self.token}"

    @task(3)
    def view_events(self):
        self.client.get("/api/v1/events/", name="GET /events/")

    @task(3)
    def view_seats(self):
        self.client.get(f"/api/v1/seats/?event_id={EVENT_ID}", name="GET /seats/")

    @task(2)
    def try_reserve(self):
        if not self.token:
            return
        r = self.client.get(f"/api/v1/seats/?event_id={EVENT_ID}", name="GET /seats/ [reserve]")
        if r.status_code != 200:
            return
        free = [s for s in r.json() if s["status"] == "FREE"]
        if not free:
            return
        seat = random.choice(free)
        self.client.post(f"/api/v1/seats/{seat['id']}/reserve/", name="POST /seats/reserve/")
