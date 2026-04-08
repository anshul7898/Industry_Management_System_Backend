import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from config.settings import APP_NAME, APP_VERSION
from routes import orders, accounts, agents, party, products, sizes, roll_sizes

# =========================================================
# ✅ Logging (Lambda-friendly)
# =========================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# =========================================================
# ✅ Initialize FastAPI app
# =========================================================
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="API for managing orders, accounts, agents, parties, and products"
)

# =========================================================
# ✅ CORS (open for now, restrict later)
# =========================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to your frontend domain later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# ✅ Include routers
# =========================================================
app.include_router(orders.router, prefix="/api", tags=["Orders"])
app.include_router(accounts.router, prefix="/api", tags=["Accounts"])
app.include_router(agents.router, prefix="/api", tags=["Agents"])
app.include_router(party.router, prefix="/api", tags=["Party"])
app.include_router(products.router, prefix="/api", tags=["Products"])
app.include_router(sizes.router, prefix="/api", tags=["Sizes"])
app.include_router(roll_sizes.router, prefix="/api", tags=["Roll Sizes"])

# =========================================================
# ✅ HEALTH CHECK
# =========================================================
@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "application": APP_NAME,
        "version": APP_VERSION
    }

# =========================================================
# ✅ ROOT
# =========================================================
@app.get("/", tags=["Root"])
def root():
    return {
        "message": f"Welcome to {APP_NAME}",
        "version": APP_VERSION,
        "docs": "/docs"
    }

# =========================================================
# ✅ Lambda handler (IMPORTANT)
# =========================================================
handler = Mangum(app, lifespan="off")

# =========================================================
# ✅ Local development
# =========================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )