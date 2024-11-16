from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.backend.db_depends import get_db
from typing import Annotated
from app.models import User, Task
from app.schemas import CreateTask, UpdateTask
from sqlalchemy import insert, select, update, delete
from slugify import slugify

router = APIRouter(prefix='/task', tags=['task'])


@router.get('/')
async def all_tasks(db: Annotated[Session, Depends(get_db)]):
    tasks = list(db.scalars(select(Task)))
    return tasks


@router.get('/{task_id}')
async def task_by_id(task_id: int, db: Annotated[Session, Depends(get_db)]):
    task = db.scalar(select(Task).where(Task.id == task_id))
    if task:
        return task
    raise HTTPException(status_code=404, detail="Task was not found")


@router.post('/create')
async def create_task(task_data: CreateTask, user_id: int, db: Annotated[Session, Depends(get_db)]):
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User was not found")

    new_task = insert(Task).values(
        title=task_data.title,
        content=task_data.content,
        priority=task_data.priority,
        user_id=user_id,
        slug=slugify(task_data.title)
    )

    db.execute(new_task)
    db.commit()

    return {'status_code': status.HTTP_201_CREATED, 'transaction': 'Successful'}


@router.put('/update')
async def update_task(task_id: int, task_data: UpdateTask, db: Annotated[Session, Depends(get_db)]):
    task_query = select(Task).where(Task.id == task_id)
    task = db.scalar(task_query)
    if task:
        update_query = (
            update(Task)
            .where(Task.id == task_id)
            .values(**task_data.dict(exclude_unset=True))
        )
        db.execute(update_query)
        db.commit()
        return {'status_code': status.HTTP_200_OK, 'transaction': 'Task update is successful!'}
    raise HTTPException(status_code=404, detail="Task was not found")


@router.delete('/delete')
async def delete_task(task_id: int, db: Annotated[Session, Depends(get_db)]):
    task_query = select(Task).where(Task.id == task_id)
    task = db.scalar(task_query)
    if task:
        delete_query = delete(Task).where(Task.id == task_id)
        db.execute(delete_query)
        db.commit()
        return {'status_code': status.HTTP_200_OK, 'transaction': 'Task deletion is successful!'}
    raise HTTPException(status_code=404, detail="Task was not found")
