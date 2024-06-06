from fastapi.testclient import TestClient
from fastapi import FastAPI
from todoapp import setting
from todoapp.main import app, get_session
from sqlmodel import SQLModel,create_engine, Session
import pytest

# Creating test database connection
connection_string = str(setting.TestTable_URL).replace("postgresql", "postgresql+psycopg")
engine = create_engine(connection_string, connect_args={"sslmode": "require"}, pool_recycle=300, pool_size=10, echo=True)

# Refactoring code with pytest fixture
@pytest.fixture(scope="module", autouse=True)
def get_db_session():
    SQLModel.metadata.create_all(engine)
    yield Session(engine)

@pytest.fixture(scope="module", autouse=True)
def test_app(get_db_session):
    def test_session():
        yield get_db_session
    app.dependency_overrides[get_session] = test_session
    with TestClient(app=app) as test_client:
        yield test_client

# Test1: root
def test_root():
    client = TestClient(app=app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to TODO app!"}
    
# Test2: post

def test_create_todo(test_app):
    # SQLModel.metadata.create_all(engine)
    # with Session(engine) as session:
    #         def db_session_override():
    #             return session
    # app.dependency_overrides[get_session] = db_session_override
    # client = TestClient(app=app)
    
    test_todo = {
        "content": "create todo test",
        "is_completed": False
    }
    response = test_app.post("/todos", json=test_todo)
    data = response.json()
    assert response.status_code == 200
    assert data["content"] == test_todo["content"]

# Test3: get all
def test_get_all_todos(test_app):
    test_todo = {
        "content": "get all todos test",
        "is_completed": False
    }
    response = test_app.post("/todos", json=test_todo)
    data = response.json()

    response = test_app.get("/todos")
    new_todo = response.json()[-1]
    assert response.status_code == 200
    assert new_todo["content"] == test_todo["content"]

# Test4: single todo
def test_get_single_todo(test_app):
    test_todo = {
        "content": "get single todo test",
        "is_completed": False
    }
    response = test_app.post("/todos", json=test_todo)
    todo_id = response.json()["id"]

    res = test_app.get(f'/todos/{todo_id}')
    data = res.json()
    assert res.status_code == 200
    assert data["content"] == test_todo["content"]

# Test5: edit todo
def test_edit_todo(test_app):
    test_todo = {
        "content": "we have edited todo test",
        "is_completed": False
    }
    response = test_app.post("/todos", json=test_todo)
    todo_id = response.json()["id"]
    
    edited_todo = {
        "content": "we have edited todo test",
        "is_completed": False
    }
    response = test_app.put(f'/todos/{todo_id}', json=edited_todo)
    data = response.json()
    assert response.status_code == 200
    assert data["content"] == edited_todo["content"]

# #Test6: delete todo
# def test_delete_todo(test_app):
#     test_todo = {
#     "content": "delete todo test", "is_completed": False
#     }
#     response = test_app.post("/todos", json=test_todo)
#     todo_id = response.json()["id"]
#     response = test_app.delete(f'/todos/{todo_id}')
#     data = response.json()
#     assert response.status_code == 200
#     assert data["message"] == "Task successfully deleted"

def test_delete_todo_item(test_app):
    # First, create a TODO item
    response = test_app.post("/todos", json={"content": "Delete TODO"})
    assert response.status_code == 200
    todo_id = response.json()["id"]

    # Then, delete the TODO item
    delete_response = test_app.delete(f"/todos/{todo_id}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"message": "Task successfully deleted"}