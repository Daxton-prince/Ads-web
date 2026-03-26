from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
import redis
import json

app = FastAPI()

# Security
API_KEY = os.getenv("API_KEY", "your-secret-key-here")
REDIS_URL = os.getenv("REDIS_URL", None)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

# CORS - Only allow your Vercel domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-site.vercel.app",  # Change this!
        "http://localhost:3000"
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis cache (optional)
if REDIS_URL:
    r = redis.from_url(REDIS_URL)
else:
    r = None

@app.get("/")
def home():
    return {"status": "alive", "message": "Downloader API"}

@app.post("/get-video")
@limiter.limit("10/minute")
async def get_video(request: Request, url: str, api_key: str = None):
    # Check API key
    if not api_key or api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Check cache
    if r:
        cached = r.get(url)
        if cached:
            return json.loads(cached)
    
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            thumbnail = info.get('thumbnail')
            title = info.get('title')
            
            formats = []
            for f in info.get('formats', []):
                if f.get('height'):
                    formats.append({
                        'quality': f'{f.get("height")}p',
                        'format': f.get('ext'),
                        'url': f.get('url'),
                    })
            
            result = {
                'success': True,
                'title': title,
                'thumbnail': thumbnail,
                'formats': formats[:5]
            }
            
            # Cache for 1 hour
            if r:
                r.setex(url, 3600, json.dumps(result))
            
            return result
            
    except Exception as e:
        return {'success': False, 'error': str(e)}