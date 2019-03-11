from starlette.applications import Starlette
from starlette.responses import JSONResponse
import json
import uvicorn
import databases
import sqlalchemy
import asyncio
from gino import Gino

# Database Management

db = Gino()
tables = ['models']

class Model(db.Model):

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "{\n" + " id: {0},\n title: {1},\n desc: {2},\n versions: {3},\n category: {4},\n params: {5},\n views: {6},\n requests: {7}\n".format(self.id, self.title, self.desc, self.versions, self.category, self.params, self.views, self.requests) + "}"

    __tablename__ = 'models'

    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String())
    desc = db.Column(db.String())
    versions = db.Column(db.ARRAY(db.Float()))
    category = db.Column(db.String())
    params = db.Column(db.ARRAY(db.JSON()))
    views = db.Column(db.Integer(), default=0)
    requests = db.Column(db.Integer(), default=0)

async def main():
    await db.set_bind('postgresql://postgres:goshilovebugs@localhost/gino')
    # await db.gino.drop(Model)
    # print('model' in db.tables)
    # print(db.gino.metadata) #, db.gino.metadata)
    # print('model' in db.tables)
    print(len(db.tables))
    # await db.gino.create_all()
    await Model.delete.gino.status()
    # model = await Model.get(4)
    # await model.delete()
    # model = await Model.create(title="test", desc="test", versions=[1.0], category="test", params=[json.dumps({"test":"test"})])
    model = await Model.query.gino.all()
    print(model)
    await db.pop_bind().close()


asyncio.get_event_loop().run_until_complete(main())