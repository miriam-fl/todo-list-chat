from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent_service import agent

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello World"}

class MessageRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_endpoint(request: MessageRequest):
    print(f"[DEBUG] Received chat request: {request.message}")
    try:
        response = await agent(request.message)
        print(f"[DEBUG] Agent response: {response}")
        return {"response": response}
    except Exception as e:
        print(f"[DEBUG] Exception in chat_endpoint: {e}")
        import traceback
        traceback.print_exc()
        return {"response": f"שגיאה: {str(e)}"}
