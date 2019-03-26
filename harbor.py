from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, PlainTextResponse, RedirectResponse
from starlette.config import Config
import json
import requests
from uvicorn import run as uvi_run
from gino import Gino
from sqlalchemy import and_

# Database Management

db = Gino()

class Model(db.Model):

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "{\n" + " id: {0},\n title: {1},\n desc: {2},\n versions: {3},\n category: {4},\n" \
                       " params: {5},\n views: {6},\n requests: {7}\n".format(
            self.id, self.title, self.desc, self.versions, self.category, self.params,
            self.views, self.requests) + "}"

    __tablename__ = 'models'

    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String())
    desc = db.Column(db.String())
    versions = db.Column(db.ARRAY(db.Float()))
    category = db.Column(db.String())
    params = db.Column(db.ARRAY(db.JSON()))
    views = db.Column(db.Integer(), default=0)
    requests = db.Column(db.Integer(), default=0)
    output_type = db.Column(db.String())
    output_attr = db.Column(db.JSON())
    clipper_model_name = db.Column(db.String())

    def to_json(self):
        return {"id": self.id, "title": self.title, "desc": self.desc, "versions": self.versions,
                "output_type": self.output_type, "clipper_model_name": self.clipper_model_name, "output_attr": self.output_attr,
                "category": self.category, "params": self.params, "views": self.views, "requests": self.requests}

models = {
    "models": Model
}

# Routing and Backend Logic

app = Starlette()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=["*"], allow_headers=["*"])
CLIPPER_URL = None

@app.on_event("startup")
async def startup():
    # Why does the example gino code make startup an async event with await? Isn't this a necessary first step?
    # This code assumes a PostgreSQL database with a name specified in the env file that has already been created
    # $ createdb gino

    harbor_config = Config('harbor.env')
    DB_USER = harbor_config('DB_USER')
    PASSWORD = harbor_config('PASSWORD')
    DB_NAME = harbor_config('DB_NAME')

    global CLIPPER_URL
    CLIPPER_URL = harbor_config('CLIPPER_URL')

    await db.set_bind('postgresql://{0}:{1}@localhost/{2}'.format(DB_USER, PASSWORD, DB_NAME))
    await db.gino.create_all(checkfirst=True)

    # user/pass may or may not be necessary, depending on OS
    # maybe should consider adding harbor user to postgreSQL as a prereq

@app.on_event("shutdown")
async def shutdown():
    await db.pop_bind().close()

@app.route('/')
async def homepage(request):
    return PlainTextResponse("Hello, world!")

@app.route('/models', methods=["GET"])
@app.route('/models/', methods=["GET"])
async def get_models(request):
    # name and category values assumed to be alphanumeric
    names = request.query_params['name'].split('+') if 'name' in request.query_params else []
    categories = request.query_params['category'].split('+') if 'category' in request.query_params else []
    if not alpha_num_validator(names + categories):
        return PlainTextResponse("400 Bad Request\nName and category values must be alphanumeric.", status_code=400)
    if names and categories:
        models = await Model.query.where(
            and_(Model.title.in_(names),
                 Model.category.in_(categories))
        ).gino.all()
    elif names:
        models = await Model.query.where(Model.title.in_(names)).gino.all()
    elif categories:
        models = await Model.query.where(Model.category.in_(categories)).gino.all()
    else:
        models = await Model.query.gino.all()
    return JSONResponse({"models": [model.to_json() for model in models]})

@app.route('/models/popular', methods=["GET"])
@app.route('/models/popular/', methods=["GET"])
async def get_popular(request):
    # optional params start_rank and count
    count = int(request.query_params.get('count', 5))
    start_rank = int(request.query_params.get('start_rank', 0))
    metric = Model.views if request.query_params.get('metric', '') == 'views' else Model.requests
    models = await Model.query.order_by(metric.desc()).offset(start_rank).limit(count).gino.all()
    return JSONResponse({"models": [model.to_json() for model in models]})

@app.route('/model')
@app.route('/model/')
async def forgot_id(request):
    return PlainTextResponse("404 Not Found\nMust provide model ID", status_code=404)

@app.route('/model/{id:int}', methods=["GET"])
@app.route('/model/{id:int}/', methods=["GET"])
async def get_model(request):
    id = request.path_params["id"]
    # if not id.isdigit():
    #     return PlainTextResponse("400 Bad Request\nMust provide integer ID.", status_code=400)
    id = int(id)
    model = await Model.get(id)
    if model is None:
        return PlainTextResponse("400 Bad Request\nModel with given ID not found", status_code=400)
    await model.update(views=model.views + 1).apply()
    return JSONResponse({id: model.to_json() if model else None})

@app.route('/query', methods=["POST", "OPTIONS"])
@app.route('/query/', methods=["POST", "OPTIONS"])
async def query_clipper(request):
    body = await request.json()
    # print(body)
    if any([elem not in body for elem in ["id", "version", "query"]]):
        return PlainTextResponse("400 Bad Request\nIncomplete query provided.")
    # will we need to query admin address of clipper to set version?
    # are there different query addresses for different models?
    # if they give us URL and image, do we need to load the image somehow?

    # Front-End Work done here:
    id = int(body["id"])
    query = body["query"]
    model = await Model.get(id)
    if model is None:
        return PlainTextResponse("400 Bad Request\nModel with given ID not found", status_code=400)
    await model.update(requests=model.requests + 1).apply()

    # Accessing Clipper
    addr = "http://18.213.175.138:1337/%s/predict" % (model.clipper_model_name)
    req_headers = {"Content-Type": "application/json"}
    req_json = json.dumps(query)
    try:
        clipperResponse = requests.post(addr, headers=req_headers, data=req_json).json()
    except:
        return JSONResponse({
            "error": "clipper returned an error",
            "req_json": req_json
        })

    # return JSONResponse({"garbage": "garbage"});
    return JSONResponse({
        "model": model.to_json() if model else None,
        "req_json": req_json,
        "url": addr,
        "data": clipperResponse
    })

@app.route('/model/create', methods=["POST"])
@app.route('/model/create/', methods=["POST"])
async def create_model(request):
    common_sad_path = PlainTextResponse("400 Bad Request\nRequired parameters not provided.", status_code=400)
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return PlainTextResponse("400 Bad Request\nPlease provide parameters in request body as a JSON.", status_code=400)
    if "version" not in body or not isinstance(body["version"], float):
        return common_sad_path
    if "id" not in body:
        if any([elem not in body for elem in ["title", "desc", "category", "params", "clipper_model_name", "output_type"]]):
            return common_sad_path
        else:
            if not isinstance(body['params'], list) or not all((isinstance(elem, dict) for elem in body['params'])):
                return common_sad_path
            await Model.create(title=body["title"], desc=body["desc"], versions=[body["version"]], clipper_model_name=body["clipper_model_name"], output_attr=["output_attr"],
                            category=body["category"], params=body["params"], output_type=body["output_type"])
    else:
        id = body["id"]
        if not isinstance(id, int):
            return common_sad_path
        model = await Model.get(id)
        if model is None:
            return common_sad_path
        ver = body["version"]
        if ver not in model.versions:
            await model.update(versions=(model.versions + [ver])).apply()
    return JSONResponse({"success": True})

def alpha_num_validator(arg):
    if isinstance(arg, list):
        return not arg or all([all([e.isalnum() for e in elem.split()]) or not elem for elem in arg])
    return arg.isalnum()

def string_is_float(num):
    return all([nums.isdigit() for nums in num.split(".")])

if __name__ == '__main__':
    uvi_run(app, host='0.0.0.0', port=8000)
