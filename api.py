from fastapi import FastAPI, Request, WebSocket
from transformers import AutoTokenizer, AutoModel
import uvicorn, json, datetime

app = FastAPI()


@app.post("/")
async def create_item(request: Request):
    global model, tokenizer
    json_post_raw = await request.json()
    json_post = json.dumps(json_post_raw)
    json_post_list = json.loads(json_post)
    prompt = json_post_list.get('prompt')
    history = json_post_list.get('history')
    response, history = model.chat(tokenizer, prompt, history=history)
    now = datetime.datetime.now()
    time = now.strftime("%Y-%m-%d %H:%M:%S")
    answer = {
        "response": response,
        "history": history,
        "status": 200,
        "time": time
    }
    log = "[" + time + "] " + '", prompt:"' + prompt + '", response:"' + repr(response) + '"'
    print(log)
    return answer


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    history = []
    while True:
        query = await websocket.receive_text()
        last = ''
        for res, history in model.stream_chat(tokenizer, query, history=history):
            if res.endswith('�'):
                continue
            await websocket.send_text(res.removeprefix(last))
            last = res


if __name__ == '__main__':
    uvicorn.run('api:app', host='0.0.0.0', port=8000, workers=1)

tokenizer = AutoTokenizer.from_pretrained("THUDM/chatglm-6b", trust_remote_code=True)
model = AutoModel.from_pretrained("THUDM/chatglm_6b", trust_remote_code=True).half().cuda()
model.eval()
