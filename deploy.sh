#!/bin/bash

# AI Recommender Deployment Script for Render

echo "🚀 Starting deployment process..."

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found. Make sure you're in the project root."
    exit 1
fi

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Error: Git not initialized. Please run 'git init' first."
    exit 1
fi

# Add all files
echo "📁 Adding files to git..."
git add .

# Check for uncommitted changes
if git diff --staged --quiet; then
    echo "ℹ️  No changes to commit."
else
    # Commit changes
    echo "💾 Committing changes..."
    git commit -m "Deploy AI Recommender to Render - $(date)"
fi

# Push to master branch
echo "📤 Pushing to master branch..."
git push origin master

echo "✅ Deployment files pushed to GitHub!"
echo ""
echo "🎯 Next steps:"
echo "1. Go to https://dashboard.render.com/"
echo "2. Click 'New +' → 'Web Service'"
echo "3. Connect your GitHub repository"
echo "4. Select master branch"
echo "5. Configure environment variables:"
echo "   - DATABASE_URL: your_postgresql_connection_string"
echo "6. Deploy!"
echo ""
echo "📚 For detailed instructions, see deploy.md"
