#!/bin/bash
set -ex

# Write the locustfile to disk
cat <<EOF >>locustfile.py
from locust import HttpLocust, TaskSet, task

class MyTaskSet(TaskSet):
    @task
    def index(self):
        print("Executing: index")
        self.client.get("/en-gb/")

    @task
    def about(self):
        print("Executing: about")
        self.client.get("/about/")

    @task
    def nutanix(self):
        print("Executing: nutanix_8")
        self.client.get("/en-gb/catalogue/category/nutanix_8/")

    @task
    def fun_stuff(self):
        print("Executing: fun-stuff_9")
        self.client.get("/en-gb/catalogue/category/nutanix/fun-stuff_9/")

    @task
    def threads(self):
        print("Executing: threads_10")
        self.client.get("/en-gb/catalogue/category/nutanix/threads_10/")

    @task
    def workspace(self):
        print("Executing: workspace_11")
        self.client.get("/en-gb/catalogue/category/nutanix/workspace_11/")

    @task
    def books(self):
        print("Executing: books")
        self.client.get("/en-gb/catalogue/category/books_2/")

    @task
    def books2(self):
        print("Executing: books page 2")
        self.client.get("/en-gb/catalogue/category/books_2/?page=2")

    @task
    def books3(self):
        print("Executing: books page 3")
        self.client.get("/en-gb/catalogue/category/books_2/?page=3")

    @task
    def books4(self):
        print("Executing: books page 4")
        self.client.get("/en-gb/catalogue/category/books_2/?page=4")

    @task
    def books5(self):
        print("Executing: books page 5")
        self.client.get("/en-gb/catalogue/category/books_2/?page=5")

    @task
    def books6(self):
        print("Executing: books page 6")
        self.client.get("/en-gb/catalogue/category/books_2/?page=6")

class MyLocust(HttpLocust):
    task_set = MyTaskSet
EOF
