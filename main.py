import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import APP_NAME, APP_VERSION, CORS_ORIGINS
from routes import orders, accounts, agents, party, products

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.error")

# Initialize FastAPI app
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="API for managing orders, accounts, agents, parties, and products"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(orders.router, prefix="/api", tags=["Orders"])
app.include_router(accounts.router, prefix="/api", tags=["Accounts"])
app.include_router(agents.router, prefix="/api", tags=["Agents"])
app.include_router(party.router, prefix="/api", tags=["Party"])
app.include_router(products.router, prefix="/api", tags=["Products"])


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "application": APP_NAME, "version": APP_VERSION}


@app.get("/", tags=["Root"])
def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {APP_NAME}",
        "version": APP_VERSION,
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )