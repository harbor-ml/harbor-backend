import json
import asyncio
from harbor import models, db
from starlette.config import Config


async def db_connect():
    print("Connecting to database...")
    harbor_config = Config('harbor.env')
    DB_USER = harbor_config('DB_USER')
    PASSWORD = harbor_config('PASSWORD')
    DB_NAME = harbor_config('DB_NAME')
    await db.set_bind('postgresql://{0}:{1}@localhost/{2}'.format(DB_USER, PASSWORD, DB_NAME))
    print("Connection made!")

async def db_disconnect():
    await db.pop_bind().close()
    print("Disconnected and finished!")

async def reset_tables(tables=None):
    if tables is None:
        await db.gino.drop_all()
    else:
        for table in tables:
            assert table in db.tables, "Table {} not found.".format(table)
        await db.gino.drop_all(tables=tables)
    await db.gino.create_all()
    print("Tables reset!")

async def seed_tables():
    with open('seed_data.json') as raw_seed_data:
        seed_data = json.load(raw_seed_data)
        for model in models:
            for model_instance in seed_data[model]:
                await models[model].create(
                    title=model_instance["title"],
                    desc=model_instance["desc"],
                    versions=[model_instance["version"]],
                    category=model_instance["category"],
                    params=model_instance["params"],
                    output_type=model_instance["output_type"],
                    clipper_model_name=model_instance["clipper_model_name"],
                    output_attr=model_instance["output_attr"]
                )
    print("Seed data has been inserted.")

async def migration():
    await db_connect()
    await reset_tables()
    await seed_tables()
    await db_disconnect()

asyncio.get_event_loop().run_until_complete(migration())
