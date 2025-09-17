# Deploy AI Recommender to Render

## 🚀 Deployment Steps

### 1. Push to GitHub

```bash
# Add all files
git add .

# Commit changes
git commit -m "Add deployment files for Render"

# Push to master branch
git push origin master
```

### 2. Deploy on Render

1. **Go to [Render Dashboard](https://dashboard.render.com/)**
2. **Click "New +" → "Web Service"**
3. **Connect your GitHub repository**
4. **Select your repository and master branch**

### 3. Configure Render Service

**Service Settings:**

- **Name**: `ai-recommender` (or your preferred name)
- **Environment**: `Python 3`
- **Region**: Choose closest to your users
- **Branch**: `master`
- **Root Directory**: Leave empty (root)
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**Environment Variables:**

- **DATABASE_URL**: Your PostgreSQL connection string
  ```
  postgresql://username:password@host:port/database?sslmode=require
  ```

### 4. Database Setup

**Option A: Use Render PostgreSQL (Recommended)**

1. Create a new PostgreSQL database on Render
2. Copy the connection string
3. Add it as DATABASE_URL environment variable

**Option B: Use External Database**

1. Use your existing Neon database
2. Add the connection string as DATABASE_URL

### 5. Run Database Migration

After deployment, run the migration script:

```bash
# SSH into your Render instance (if needed)
# Or run locally with production DATABASE_URL
python migrate_products_interaction.py
```

### 6. Test Your Deployment

Your API will be available at:

```
https://your-app-name.onrender.com
```

**Test endpoints:**

```bash
# Health check
curl https://your-app-name.onrender.com/

# API docs
https://your-app-name.onrender.com/docs

# Create product
curl -X POST "https://your-app-name.onrender.com/api/v1/products" \
     -H "Content-Type: application/json" \
     -d '{
       "product_id": "test-123",
       "name": "Test Product",
       "description": "Test description",
       "price": 29.99,
       "stock": 100,
       "category": "Test Category",
       "user_id": "user123",
       "interaction_type": "view",
       "interaction_weight": 1.0
     }'
```

## 🔧 Configuration Files Created

- `render.yaml` - Render service configuration
- `Procfile` - Process file for web service
- `runtime.txt` - Python version specification
- `Dockerfile` - Docker configuration (optional)
- `.dockerignore` - Docker ignore file
- `requirements.txt` - Updated with gunicorn

## 📝 Environment Variables

Make sure to set these in Render dashboard:

- `DATABASE_URL` - Your PostgreSQL connection string
- `PYTHON_VERSION` - 3.11.0 (optional)

## 🎯 Frontend Integration

Once deployed, update your frontend to use the new API URL:

```javascript
// Update your frontend API base URL
const API_BASE_URL = "https://your-app-name.onrender.com";

// Example API calls
const response = await fetch(`${API_BASE_URL}/api/v1/products`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify(productData),
});
```

## 🚨 Important Notes

1. **Free Tier Limitations**: Render free tier has sleep mode after 15 minutes of inactivity
2. **Database Migration**: Run migration script after deployment
3. **Environment Variables**: Set DATABASE_URL in Render dashboard
4. **CORS**: Add your frontend domain to CORS if needed
5. **Logs**: Check Render logs for any deployment issues

## 🔍 Troubleshooting

**Common Issues:**

- **Build fails**: Check requirements.txt and Python version
- **Database connection**: Verify DATABASE_URL format
- **Import errors**: Ensure all dependencies are in requirements.txt
- **Port issues**: Use `$PORT` environment variable in start command

**Check Logs:**

- Go to Render dashboard → Your service → Logs
- Look for error messages and stack traces
