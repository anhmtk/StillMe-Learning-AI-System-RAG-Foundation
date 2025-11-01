# 🚀 Deploy StillMe Public Dashboard - Quick Guide

## **⚡ 5-Minute Deploy với Railway.app**

### **Step 1: Push Code to GitHub**
```bash
git push origin main
```
✅ Code đã có sẵn config files!

### **Step 2: Deploy on Railway**
1. Vào https://railway.app
2. Login với GitHub
3. Click **"New Project"** → **"Deploy from GitHub repo"**
4. Chọn repo: `StillMe---Self-Evolving-AI-System`
5. Railway tự động detect `docker-compose.yml` ✅

### **Step 3: Set Environment Variables**
Trong Railway dashboard, thêm:
```
DEEPSEEK_API_KEY=sk-your-key
OPENAI_API_KEY=sk-your-key
```

### **Step 4: Done! 🎉**
Railway tự động:
- ✅ Build Docker image
- ✅ Deploy services (backend + dashboard)
- ✅ Assign public URLs
- ✅ Enable HTTPS (tự động)

**URLs bạn nhận được:**
- Dashboard: `https://stillme-dashboard.railway.app`
- API: `https://stillme-backend.railway.app`

---

## **✨ Alternative: Render.com (Free)**

1. Vào https://render.com
2. Login với GitHub
3. **"New"** → **"Web Service"** → Connect repo
4. Render tự động detect `render.yaml` ✅
5. Set environment variables
6. Deploy!

**URL:** `https://stillme-dashboard.onrender.com`

---

## **📁 Config Files Included**

Các file này đã có sẵn trong repo:
- ✅ `railway.json` - Railway config
- ✅ `render.yaml` - Render config  
- ✅ `docker-compose.yml` - Docker services
- ✅ `Procfile` - Heroku config (optional)
- ✅ `.railwayignore` - Ignore unnecessary files

**Bạn chỉ cần: Connect GitHub → Deploy!**

---

## **💰 Cost**

**Railway:**
- Free: $5 credit/month (đủ dùng)
- Paid: ~$5/month nếu hết free

**Render:**
- Free: 750 hours/month (24/7 trong 1 tháng)
- Paid: $7/month nếu muốn always-on

**Recommendation:** Railway (dễ nhất, free tier tốt)

---

## **🔧 Troubleshooting**

**Problem: Build fails**
- Check logs trong Railway/Render dashboard
- Verify `requirements.txt` có đủ dependencies
- Check Python version (3.12+)

**Problem: Dashboard không kết nối backend**
- Verify `STILLME_API_BASE` env var đúng URL
- Check backend service đã start chưa

**Problem: Environment variables không work**
- Set trong platform dashboard (Railway/Render)
- Không commit `.env` file (đã có trong `.gitignore`)

---

## **📊 After Deployment**

**Community sẽ thấy:**
- ✅ Public dashboard với live metrics
- ✅ Evolution progress real-time
- ✅ Vector DB stats
- ✅ Learning performance

**Cùng 1 dashboard cho tất cả!** 🌍

---

**Need help?** Open an issue trên GitHub!

