// This file goes in: /api/download.js
export default async function handler(req, res) {
    // Enable CORS
    res.setHeader('Access-Control-Allow-Origin', '*');
    
    const { url } = req.query;
    
    if (!url) {
        return res.status(400).json({ error: 'URL required' });
    }
    
    try {
        // Get Railway URL and API key from environment
        const RAILWAY_URL = process.env.RAILWAY_URL;
        const API_KEY = process.env.API_KEY;
        
        // Call Railway securely
        const response = await fetch(
            `${RAILWAY_URL}/get-video?url=${encodeURIComponent(url)}&api_key=${API_KEY}`,
            { method: 'POST' }
        );
        
        const data = await response.json();
        res.json(data);
        
    } catch (error) {
        res.status(500).json({ error: 'Failed to process' });
    }
}
