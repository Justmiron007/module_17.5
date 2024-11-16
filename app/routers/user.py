from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.backend.db_depends import get_db
from typing import Annotated
from app.models import User, Task
from app.schemas import CreateUser, UpdateUser
from sqlalchemy import insert, select, update, delete
from slugify import slugify

router = APIRouter(prefix='/user', tags=['user'])


@router.get('/')
async def all_users(db: Annotated[Session, Depends(get_db)]):
    users = list(db.scalars(select(User)))
    return users


@router.get('/{user_id}')
async def user_by_id(user_id: int, db: Annotated[Session, Depends(get_db)]):
    user = db.scalar(select(User).where(User.id == user_id))
    if user:
        return user
    raise HTTPException(status_code=404, detail="User was not found")


@router.get('/{user_id}/tasks')
async def tasks_by_user_id(user_id: int, db: Annotated[Session, Depends(get_db)]):
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User was not found")

    tasks = list(db.scalars(select(Task).where(Task.user_id == user_id)))
    return tasks


@router.post('/create')
async def create_user(user_data: CreateUser, db: Annotated[Session, Depends(get_db)]):
    existing_user = db.execute(
        select(User).where(User.username == user_data.username)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this username already exists."
        )

    new_user = insert(User).values(
        username=user_data.username,
        firstname=user_data.firstname,
        lastname=user_data.lastname,
        age=user_data.age,
        slug=slugify(user_data.username)
    )
    db.execute(new_user)
    db.commit()

    return {'status_code': status.HTTP_201_CREATED, 'transaction': 'Successful'}


@router.put('/update')
async def update_user(user_id: int, user_data: UpdateUser, db: Annotated[Session, Depends(get_db)]):
    user_query = select(User).where(User.id == user_id)
    user = db.scalar(user_query)
    if user:
        update_query = (
            update(User)
            .where(User.id == user_id)
            .values(**user_data.dict(exclude_unset=True))
        )
        db.execute(update_query)
        db.commit()
        return {'status_code': status.HTTP_200_OK, 'transaction': 'User update is successful!'}
    raise HTTPException(status_code=404, detail="User was not found")


@router.delete('/delete')
async def delete_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    user_query = select(User).where(User.id == user_id)
    user = db.scalar(user_query)
    if user:
        delete_tasks_query = delete(Task).where(Task.user_id == user_id)
        db.execute(delete_tasks_query)

        delete_user_query = delete(User).where(User.id == user_id)
        db.execute(delete_user_query)

        db.commit()
        return {'status_code': status.HTTP_200_OK, 'transaction': 'User and related tasks deletion is successful!'}
    raise HTTPException(status_code=404, detail="User was not found")
