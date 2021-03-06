# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import os
import unittest
from datetime import datetime

from airflow import DAG
from airflow.models import DagBag
from airflow.models.serialized_dag import SerializedDagModel
from airflow.operators.dummy_operator import DummyOperator
from airflow.www import app
from tests.test_utils.config import conf_vars
from tests.test_utils.db import clear_db_dags, clear_db_runs, clear_db_serialized_dags


class TestTaskEndpoint(unittest.TestCase):
    dag_id = "test_dag"
    task_id = "op1"

    @staticmethod
    def clean_db():
        clear_db_runs()
        clear_db_dags()
        clear_db_serialized_dags()

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.app = app.create_app(testing=True)  # type:ignore

        with DAG(cls.dag_id, start_date=datetime(2020, 6, 15), doc_md="details") as dag:
            DummyOperator(task_id=cls.task_id)

        cls.dag = dag  # type:ignore
        dag_bag = DagBag(os.devnull, include_examples=False)
        dag_bag.dags = {dag.dag_id: dag}
        cls.app.dag_bag = dag_bag  # type:ignore

    def setUp(self) -> None:
        self.clean_db()
        self.client = self.app.test_client()  # type:ignore

    def tearDown(self) -> None:
        self.clean_db()


class TestGetTask(TestTaskEndpoint):
    def test_should_response_200(self):
        expected = {
            "class_ref": {
                "class_name": "DummyOperator",
                "module_path": "airflow.operators.dummy_operator",
            },
            "depends_on_past": False,
            "downstream_task_ids": [],
            "end_date": None,
            "execution_timeout": None,
            "extra_links": [],
            "owner": "airflow",
            "pool": "default_pool",
            "pool_slots": 1.0,
            "priority_weight": 1.0,
            "queue": "default",
            "retries": 0.0,
            "retry_delay": {"__type": "TimeDelta", "days": 0, "seconds": 300, "microseconds": 0},
            "retry_exponential_backoff": False,
            "start_date": "2020-06-15T00:00:00+00:00",
            "task_id": "op1",
            "template_fields": [],
            "trigger_rule": "all_success",
            "ui_color": "#e8f7e4",
            "ui_fgcolor": "#000",
            "wait_for_downstream": False,
            "weight_rule": "downstream",
        }
        response = self.client.get(f"/api/v1/dags/{self.dag_id}/tasks/{self.task_id}")
        assert response.status_code == 200
        assert response.json == expected

    @conf_vars({("core", "store_serialized_dags"): "True"})
    def test_should_response_200_serialized(self):
        # Create empty app with empty dagbag to check if DAG is read from db
        app_serialized = app.create_app(testing=True)  # type:ignore
        dag_bag = DagBag(os.devnull, include_examples=False, store_serialized_dags=True)
        app_serialized.dag_bag = dag_bag  # type:ignore
        client = app_serialized.test_client()

        SerializedDagModel.write_dag(self.dag)

        expected = {
            "class_ref": {
                "class_name": "DummyOperator",
                "module_path": "airflow.operators.dummy_operator",
            },
            "depends_on_past": False,
            "downstream_task_ids": [],
            "end_date": None,
            "execution_timeout": None,
            "extra_links": [],
            "owner": "airflow",
            "pool": "default_pool",
            "pool_slots": 1.0,
            "priority_weight": 1.0,
            "queue": "default",
            "retries": 0.0,
            "retry_delay": {"__type": "TimeDelta", "days": 0, "seconds": 300, "microseconds": 0},
            "retry_exponential_backoff": False,
            "start_date": "2020-06-15T00:00:00+00:00",
            "task_id": "op1",
            "template_fields": [],
            "trigger_rule": "all_success",
            "ui_color": "#e8f7e4",
            "ui_fgcolor": "#000",
            "wait_for_downstream": False,
            "weight_rule": "downstream",
        }
        response = client.get(f"/api/v1/dags/{self.dag_id}/tasks/{self.task_id}")
        assert response.status_code == 200
        assert response.json == expected

    def test_should_response_404(self):
        task_id = "xxxx_not_existing"
        response = self.client.get(f"/api/v1/dags/{self.dag_id}/tasks/{task_id}")
        assert response.status_code == 404


class TestGetTasks(TestTaskEndpoint):
    def test_should_response_200(self):
        expected = {
            "tasks": [
                {
                    "class_ref": {
                        "class_name": "DummyOperator",
                        "module_path": "airflow.operators.dummy_operator",
                    },
                    "depends_on_past": False,
                    "downstream_task_ids": [],
                    "end_date": None,
                    "execution_timeout": None,
                    "extra_links": [],
                    "owner": "airflow",
                    "pool": "default_pool",
                    "pool_slots": 1.0,
                    "priority_weight": 1.0,
                    "queue": "default",
                    "retries": 0.0,
                    "retry_delay": {"__type": "TimeDelta", "days": 0, "seconds": 300, "microseconds": 0},
                    "retry_exponential_backoff": False,
                    "start_date": "2020-06-15T00:00:00+00:00",
                    "task_id": "op1",
                    "template_fields": [],
                    "trigger_rule": "all_success",
                    "ui_color": "#e8f7e4",
                    "ui_fgcolor": "#000",
                    "wait_for_downstream": False,
                    "weight_rule": "downstream",
                }
            ],
            "total_entries": 1,
        }
        response = self.client.get(f"/api/v1/dags/{self.dag_id}/tasks")
        assert response.status_code == 200
        assert response.json == expected

    def test_should_response_404(self):
        dag_id = "xxxx_not_existing"
        response = self.client.get(f"/api/v1/dags/{dag_id}/tasks")
        assert response.status_code == 404
