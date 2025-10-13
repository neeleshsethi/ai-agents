from fastapi import FastAPI
from contextlib import asynccontextmanager



async def load_data():
    print("Loaded data in db")


async def my_model(x: float):
    return x ** 2

async def clear_db():
    print("Cleared db")

ml_models = {}

@asynccontextmanager
async def lifespan():
    await load_data()
    ml_models["my_model"] = my_model
    yield
    ml_models.clear()
    await clear_db()

app = FastAPI(lifespan=lifespan)

async def predict(x: float):
    result = await ml_models["my_model"](x)
    return result