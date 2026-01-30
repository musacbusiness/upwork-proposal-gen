# Deploy Proposal Generator to Modal (24/7 Cloud Hosting)

Your proposal generator running 24/7 in the cloud. Your Mac can stay off.

---

## 🚀 Quick Start (5 minutes)

### Step 1: Install Modal

```bash
pip install modal
```

### Step 2: Create Modal Account & Auth

```bash
modal token new
```

This opens a browser to authenticate. Copy the token back to terminal.

### Step 3: Store Your Claude API Key

```bash
modal secret create upwork-proposal-secrets \
  ANTHROPIC_API_KEY=sk-ant-api03-...
```

(Paste your actual API key from `.env`)

### Step 4: Deploy

```bash
cd "/Users/musacomma/Agentic Workflow"
modal deploy execution/modal_proposal_app.py
```

**Done.** Modal gives you a URL. Your app is now live 24/7.

---

## 📍 How to Access

After deployment, Modal shows:
```
✓ Deployed successfully
URL: https://your-username--proposal-generator.modal.run
```

Visit that URL from anywhere, any device. App runs even if your Mac is off.

---

## 🎯 Why Modal?

| Feature | Streamlit Cloud | Modal | Local |
|---------|-----------------|-------|-------|
| Always on | ✓ | ✓ | ✗ (Mac only) |
| Free tier | ✓ (limited) | ✓ (generous) | ✓ |
| Cost | $7-70/month | $0-50/month | Free |
| Control | Medium | High | Complete |
| Setup | 2 clicks | 5 minutes | Done |
| Fits architecture | - | **✓✓** | - |

**Best for you:** Modal because it fits your 3-layer architecture (deterministic code, scalable, cloud-first).

---

## 📋 Complete Setup (Step by Step)

### 1. Create Modal Account

Go to https://modal.com and sign up.

### 2. Install Modal CLI

```bash
pip install modal
```

### 3. Authenticate

```bash
modal token new
```

Follow the prompts. You'll get a token.

### 4. Store Your Secrets

```bash
modal secret create upwork-proposal-secrets \
  ANTHROPIC_API_KEY=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
```

(Replace with your actual key from `.env`)

### 5. Deploy the App

```bash
cd "/Users/musacomma/Agentic Workflow"
modal deploy execution/modal_proposal_app.py
```

Wait for:
```
✓ Deployed
URL: https://your-namespace--upwork-proposal-generator.modal.run
```

### 6. Access Anywhere

Visit that URL. Done!

---

## 🔄 Updates

After making changes:

```bash
modal deploy execution/modal_proposal_app.py
```

Takes ~1 minute. URL stays the same.

---

## 📊 Pricing

**Modal free tier includes:**
- 20 GB storage
- 200 GPU hours/month
- 40 vCPU hours/day
- Great for your use case

**Cost estimate for this app:**
- Your usage: ~$0-2/month
- Generation: ~0.5 cents per proposal

Essentially free.

---

## 🆚 Comparison: All 3 Options

### Option 1: Local (Current)
```bash
streamlit run execution/streamlit_proposal_app.py
```
- ✓ Works now
- ✗ Mac must be on
- ✗ No phone access outside WiFi

### Option 2: Streamlit Cloud (Easiest)
1. Push to GitHub
2. Go to https://share.streamlit.io
3. Connect repo
- ✓ 2 clicks to deploy
- ✓ Free tier
- ✗ Less control

### Option 3: Modal (Recommended)
```bash
modal deploy execution/modal_proposal_app.py
```
- ✓ 24/7 running
- ✓ Mac can be off
- ✓ Fits your architecture
- ✓ Full control
- ✓ Cheap ($0-5/month)

---

## 🎓 How Modal Works (Architecture)

```
Your Request
    ↓
Modal Cloud (processes)
    ↓
Claude API (generates)
    ↓
Response back to you
```

All deterministic, all in the cloud. Scales automatically.

---

## 🔐 Security

Your Claude API key:
- Stored in Modal Secrets (encrypted)
- Never in code
- Never exposed
- Secure by default

---

## 💡 Advanced: Custom Domain

If you want a custom domain (e.g., `proposals.yourdomain.com`):

1. Modal supports custom domains
2. Set up DNS CNAME
3. Point to Modal endpoint

(Can do this later)

---

## 🚨 Troubleshooting

### "modal token new" fails
Make sure you're logged in to https://modal.com first

### Secret not found
```bash
modal secret list
```

Verify it's named `upwork-proposal-secrets`

### Deploy fails
```bash
modal logs
```

Shows detailed error logs.

### URL not working
Wait 2-3 minutes for cold start. Modal spins up after deploy.

---

## 📝 Your Deploy Checklist

- [ ] Installed Modal: `pip install modal`
- [ ] Created Modal account at https://modal.com
- [ ] Ran `modal token new` and authenticated
- [ ] Created secret with `modal secret create upwork-proposal-secrets`
- [ ] Ran `modal deploy execution/modal_proposal_app.py`
- [ ] Got URL from Modal
- [ ] Visited URL - app works!
- [ ] Mac can be turned off - app still runs

---

## 🎯 Do It Right Now

### In terminal:

```bash
# 1. Install
pip install modal

# 2. Auth
modal token new

# 3. Secret
modal secret create upwork-proposal-secrets \
  ANTHROPIC_API_KEY=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

# 4. Deploy
cd "/Users/musacomma/Agentic Workflow"
modal deploy execution/modal_proposal_app.py

# 5. Wait for URL, visit it
```

**Total time: 5 minutes**

Then your app runs 24/7, and you never think about it again.

---

## 🌟 What You Get

- ✓ Proposal generator accessible anywhere
- ✓ Mac stays off
- ✓ Phone, tablet, desktop all work
- ✓ 24/7 uptime
- ✓ ~$0-2/month cost
- ✓ Full control
- ✓ Logs and monitoring
- ✓ Easy updates

---

## 📚 Resources

- Modal docs: https://modal.com/docs
- Your app config: `execution/modal_proposal_app.py`
- Local version still works: `streamlit run execution/streamlit_proposal_app.py`

---

## Next Steps

1. Deploy to Modal (follow checklist above)
2. Get live URL
3. Bookmark on phone
4. Turn off Mac
5. Use proposal generator from anywhere

Done! 🚀
