# Render Deployment Guide for AI Trip Planner MCP Server

## Quick Deploy to Render

### Method 1: Using Render Dashboard (Recommended)

1. **Connect Repository**:
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository: `Himanshujchavan/MCP_TRAVEL`

2. **Configure Service**:
   - **Name**: `ai-trip-planner-mcp`
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python mcp_http_server.py`

3. **Environment Variables** (Add these in Render dashboard):
   ```
   AUTH_TOKEN=oAGVDZtqPIqnhSoyJiPrBTsfKeCN_gsUmrqZZRxeYwE
   MCP_BEARER_TOKEN=oAGVDZtqPIqnhSoyJiPrBTsfKeCN_gsUmrqZZRxeYwE
   MY_NUMBER=1234567890
   MCP_HTTP_HOST=0.0.0.0
   SKYSCANNER_API_KEY=your_real_api_key_here
   BOOKING_API_KEY=your_real_api_key_here
   WEATHER_API_KEY=your_real_api_key_here
   GOOGLE_PLACES_API_KEY=your_real_api_key_here
   ```

4. **Deploy**: Click "Create Web Service"

### Method 2: Using render.yaml (Blueprint)

1. In your Render dashboard, click "New +" → "Blueprint"
2. Connect your repository
3. Render will automatically detect the `render.yaml` file
4. Review and deploy

### Method 3: Docker Deployment

1. In Render dashboard, choose "Docker" as runtime
2. Dockerfile is already configured in the repo
3. Set PORT environment variable (Render will do this automatically)

## Important Notes

### Port Configuration
- Render automatically assigns a PORT environment variable
- Our server listens on the PORT provided by Render
- Local development uses port 8086, production uses Render's assigned port

### API Keys
- Update the placeholder API keys with real ones for full functionality
- Demo keys are set for basic testing
- Add real API keys in Render environment variables for production

### Health Check
- Health check endpoint available at `/health`
- Returns: `{"status": "healthy", "service": "AI Trip Planner MCP Server"}`

### MCP Access
- Once deployed, your MCP server will be available at:
  `https://your-app-name.onrender.com/mcp/`
- Use the bearer token for authentication: `oAGVDZtqPIqnhSoyJiPrBTsfKeCN_gsUmrqZZRxeYwE`

## Troubleshooting

### Build Failures
- Check that `requirements.txt` is present and properly formatted
- Ensure Python 3.12 is specified in `runtime.txt`
- Verify all imports in the code are available in requirements

### Runtime Errors
- Check environment variables are set correctly
- Verify the bearer token is configured
- Monitor logs in Render dashboard

### Connection Issues
- Ensure the server binds to `0.0.0.0` (not `localhost`)
- Verify PORT environment variable is being used
- Check firewall/security group settings if using custom domains

## Deployment Commands

If you prefer command-line deployment:

```bash
# Install Render CLI
npm install -g @render/cli

# Login to Render
render login

# Deploy using blueprint
render blueprint deploy
```

## Success Indicators

✅ Build completes without errors
✅ Health check returns 200 OK at `/health`
✅ MCP tools are accessible at `/mcp/tools/list`
✅ Authentication works with bearer token
✅ All 8 travel planning tools are available

Your AI Trip Planner MCP Server will be ready for AI agents to connect and use!
