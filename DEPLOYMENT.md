# Deployment Guide

## Vercel Frontend Deployment

### Environment Variables Required in Vercel:

1. Go to your Vercel project settings
2. Add the following environment variables:

```
REACT_APP_BACKEND_URL=https://your-backend-app.onrender.com
```

Replace `your-backend-app.onrender.com` with your actual Render backend URL.

### Node.js Version:

- Set Node.js version to **20.x** in Vercel Project Settings
- The `vercel.json` file specifies Node.js 20 for this deployment

## Render Backend Deployment

### Environment Variables Required in Render:

```
OPENAI_API_KEY=your_openai_api_key
MONGO_URL=your_mongodb_connection_string
DB_NAME=your_database_name
CORS_ORIGINS=https://your-vercel-app.vercel.app
```

### Important Notes:

1. **CORS Configuration**: Update `CORS_ORIGINS` to include your Vercel domain
2. **Database**: Ensure MongoDB is accessible from Render
3. **OpenAI**: Make sure your OpenAI API key has sufficient credits

## Common Issues and Solutions

### Node.js Version Errors:
- ✅ Fixed: Added `engines` specification in package.json
- ✅ Fixed: Added `vercel.json` with Node.js 20 specification

### Build Failures:
- ✅ Fixed: Updated ajv dependency to resolve conflicts
- ✅ Fixed: Added proper build configuration

### CORS Errors:
- Ensure `CORS_ORIGINS` includes your Vercel domain
- Format: `https://your-app-name.vercel.app`

### API Connection Issues:
- Verify `REACT_APP_BACKEND_URL` is correct
- Test backend health: `curl https://your-backend.onrender.com/api/`

## Testing Deployment

1. **Backend Health Check:**
   ```bash
   curl https://your-backend.onrender.com/api/
   ```

2. **Frontend Build Test:**
   ```bash
   cd frontend
   npm run build
   ```

3. **Environment Variables:**
   - Check Vercel dashboard for all required variables
   - Ensure backend URL is accessible

## Troubleshooting

### If you see Node.js deprecation warnings:
- Update Node.js version to 20.x in Vercel settings
- The `vercel.json` file should handle this automatically

### If API calls fail:
- Check CORS configuration in backend
- Verify environment variables are set correctly
- Test backend endpoint directly

### If build fails:
- Check for dependency conflicts
- Ensure all required environment variables are set
- Review build logs in Vercel dashboard 