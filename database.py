from sqlalchemy import create_engine,ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column,sessionmaker,relationship
from datetime import date
from typing import Optional

engine = create_engine("sqlite:///workouts.db")
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

class WorkoutDB(Base):
    __tablename__ = "workouts"

    id: Mapped[int] = mapped_column(primary_key=True)
    workout_date: Mapped[date]
    exercises: Mapped[list["ExerciseDB"]] = relationship(back_populates="workout")

class ExerciseDB(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    workout_id: Mapped[int] = mapped_column(ForeignKey("workouts.id"))
    exercise: Mapped[str]
    sets: Mapped[int | None]
    reps: Mapped[int | None]
    weight: Mapped[float | None]
    unit: Mapped[str | None]
    rpe: Mapped[int | None]
    workout: Mapped["WorkoutDB"] = relationship(back_populates="exercises")

Base.metadata.create_all(engine)