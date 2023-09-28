import os
import json
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

# Replace this with your PostgreSQL database URL
DATABASE_URL = "postgresql://postgres@localhost:5432/task_management_tool"

Base = declarative_base()

# Replace the placeholders with your actual database credentials
DATABASE_URL = "postgresql://postgres@localhost:5432/task_management_tool"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

TASK_FILE = "tasks.json"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)


Base.metadata.create_all(engine)


def reset_sequence():
    # Replace 'tasks' with the name of your table and 'id' with the name of the primary key column
    TABLE_NAME = "tasks"
    PRIMARY_KEY_COLUMN = "id"

    # Query the database for the sequence name
    sequence_name_query = text(
        f"SELECT column_default FROM information_schema.columns WHERE table_name = '{TABLE_NAME}' AND column_name = '{PRIMARY_KEY_COLUMN}';"
    )

    # Create a connection to the database
    connection = engine.connect()

    # Execute the query to get the sequence name
    result = connection.execute(sequence_name_query)
    row = result.fetchone()
    sequence_name = row[0].split("'")[
        1
    ]  # Extract the sequence name from the column_default value

    # Generate the SQL command to reset the correct sequence
    reset_sequence_sql = text(f"ALTER SEQUENCE {sequence_name} RESTART WITH 1;")

    # Execute the SQL command
    connection.execute(reset_sequence_sql)

    # Close the connection
    connection.close()


def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


def load_tasks(db):
    if os.path.exists(TASK_FILE):
        with open(TASK_FILE, "r") as file:
            try:
                tasks = json.load(file)
            except json.JSONDecodeError as e:
                print(f"Error loading JSON data: {e}")
                tasks = []
    else:
        tasks = []

    if tasks:
        return tasks
    else:
        return []


def save_tasks(tasks):
    db = get_db()
    db.query(Task).delete()  # Remove all existing tasks
    db.add_all([Task(name=t["name"], description=t["description"]) for t in tasks])
    db.commit()
    with open(TASK_FILE, "w") as file:
        json.dump(tasks, file)


def list_tasks(db):
    tasks = load_tasks(db)
    if tasks:
        print("Tasks: ")
        for i, task in enumerate(tasks, 1):
            print(f"{i}. {task['name']} - {task['description']}")
    else:
        print("No tasks found.")


def add_task(db, name, description):
    task = {"name": name, "description": description}
    tasks = load_tasks(db)
    tasks.append(task)
    save_tasks(tasks)
    print(f"Task '{name}' added successfully!")


def delete_task(db, task_id):
    task_id -= 1  # Adjust task_id to account for 0-based indexing in the JSON list
    tasks = load_tasks(db)
    if 0 <= task_id < len(tasks):
        deleted_task = tasks.pop(task_id)
        save_tasks(tasks)
        reset_sequence()
        print(f"Task '{deleted_task['name']}' deleted successfully!")
    else:
        print("Invalid task ID.")


def main():
    db = get_db()
    while True:
        print("\nTaskify")
        print("1. List Tasks")
        print("2. Add Task")
        print("3. Delete Task")
        print("4. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            list_tasks(db)
        elif choice == "2":
            name = input("Enter task name: ")
            description = input("Enter task description: ")
            add_task(db, name, description)
        elif choice == "3":
            task_id = int(input("Enter the task ID to delete: "))
            delete_task(db, task_id)
        elif choice == "4":
            print("Exiting")
            break
        else:
            print("Invalid choice. Please try again.")

    db.close()


if __name__ == "__main__":
    main()
