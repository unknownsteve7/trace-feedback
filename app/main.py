from fastapi import FastAPI
import uvicorn
import dotenv

dotenv.load_dotenv()

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Welcome to the QR code feedback service"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="[IP_ADDRESS]", port=8000, reload=True)

