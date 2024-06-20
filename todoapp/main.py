from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import SQLModel, Field, create_engine, Session, select
from todoapp import setting
from typing import Annotated
from contextlib import asynccontextmanager, contextmanager

#ALL STEPS
# step1 Crete database on neon
# step2 create .env file for enviroment variables
# step3 create setting.py file for encrypted database url
# step4 create a Model
# step5 create engine
# setp6 create function for table creation
# step7 create function for session management
# step8 create context manager for lifespan
# step9 create all endpoints/routes of todo app



# Create Model / create table

class TODO (SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True, nullable=False,)
    content: str = Field (index=True, min_length=5, max_length=54)
    is_completed: bool = Field(default=False)

# creating database connection
connection_string : str = str(setting.DATABASE_URL).replace("postgresql", "postgresql+psycopg")
engine = create_engine(connection_string, connect_args={"sslmode":"require"}, pool_recycle=300, pool_size=10, echo=False)

def create_tables():
    SQLModel.metadata.create_all(engine)

# test code
# todo1: TODO = TODO(content="first task")
# todo2: TODO = TODO(content="second task")
# session = Session(engine)
# session.add(todo1)
# session.add(todo2)
# session.commit()
# session.refresh(todo1)
# print(f'AFTER commit {todo1} and {todo2}')
# session.close()

#creating session
def get_session():
    with Session(engine) as session:
        yield session
        
@asynccontextmanager
async def lifespan(app: FastAPI):
    print('Creating tables')
    create_tables()
    print('Tables created')
    yield
# start app
app: FastAPI = FastAPI(lifespan=lifespan, 
    title="TODO APP", 
    version="1.0.0",
    servers=[{"url": "http://0.0.0.0:8000",
    "description": "Development server"}]
    
    )

# setting root message
@app.get("/")
async def root():
    return {"message": "Welcome to TODO app!"}

#creating post route
@app.post("/todos")
async def create_todo(todo: TODO, session:Annotated[Session,Depends(get_session)]):
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo 
    
#creating get all route
@app.get("/todos", response_model=list[TODO])
async def get_all_todos(session:Annotated[Session,Depends(get_session)]):
    todos = session.exec(select(TODO)).all()
    if todos:
        return todos
    else:
        raise HTTPException(status_code=404, detail="TODO not found")  


#creating get route with id
@app.get('/todos/{id}', response_model=TODO)
async def get_single_todo(id: int, session:Annotated[Session,Depends(get_session)]):
    todo = session.exec(select(TODO).where(TODO.id == id)).first()
    if todo:
        return todo
    else:
        raise HTTPException(status_code=404, detail="TODO not found")
    

#creating update route
@app.put('/todos/{id}')
async def update_todo(todo:TODO, id:int, session:Annotated[Session,Depends(get_session)]):
    existing_todo = session.exec(select(TODO).where(TODO.id == id)).first()
    if existing_todo:
        existing_todo.content == todo.content
        existing_todo.is_completed = todo.is_completed
        session.add(existing_todo)
        session.commit()
        session.refresh(existing_todo)
        return existing_todo
    else:
        raise HTTPException(status_code=404, detail="TODO not found")
    
    
#creating delete route
@app.delete('/todos/{id}')
async def delete_todo(id:int, session:Annotated[Session,Depends(get_session)]):
    todo = session.exec(select(TODO).where(TODO.id == id)).first()
    if todo:
        session.delete(todo)
        session.commit()
        return {"message": "Task successfully deleted"}
    else:
        raise HTTPException(status_code=404, detail="TODO not found")
