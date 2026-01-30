# Quick Reference - Upwork Proposal Generator

## 🚀 Run Locally (Right Now)

```bash
cd "/Users/musacomma/Agentic Workflow"
streamlit run execution/streamlit_proposal_app.py
```

Then:
1. Open `http://localhost:8501`
2. Paste Upwork job URL
3. Click "Generate"
4. Copy to clipboard

---

## ☁️ Deploy to Cloud (8 Min Setup)

```bash
bash deploy.sh
```

Follow prompts:
1. Authenticate Modal
2. Enter Claude API key
3. Wait for deployment

Then:
1. Push code to GitHub
2. Go to https://share.streamlit.io
3. Connect repo
4. Done - live at `https://your-username-proposal-gen.streamlit.app`

---

## 📁 Key Files

| File | What |
|------|------|
| `execution/streamlit_proposal_app.py` | Web interface |
| `execution/generate_upwork_proposal.py` | Core logic |
| `.env` | Your API keys |
| `requirements.txt` | Dependencies |
| `deploy.sh` | Automated deployment |

---

## 📖 Guides

| Guide | When |
|-------|------|
| [README_PROPOSAL_GENERATOR.md](README_PROPOSAL_GENERATOR.md) | Start here - overview |
| [DEPLOY_MODAL_STREAMLIT.md](DEPLOY_MODAL_STREAMLIT.md) | Deploy to cloud |
| [PROPOSAL_GENERATOR_GUIDE.md](PROPOSAL_GENERATOR_GUIDE.md) | How to use |
| [HOSTING_COMPARISON.md](HOSTING_COMPARISON.md) | Which option |

---

## 🔑 Commands

```bash
# Run locally
streamlit run execution/streamlit_proposal_app.py

# Deploy to cloud (automated)
bash deploy.sh

# Deploy to Modal only
modal deploy execution/generate_upwork_proposal.py

# View Modal logs
modal logs upwork-proposal-generator

# Check Modal secrets
modal secret list

# Install dependencies
pip install -r requirements.txt
```

---

## 🎯 Workflow

1. **See job** → Copy URL
2. **Open app** → Localhost or cloud URL
3. **Paste URL** → Or description
4. **Generate** → 10 seconds
5. **Copy** → One click
6. **Paste in Upwork** → Done
7. **Submit** → You win

---

## 💰 Costs

- **Local:** $0/month
- **Streamlit Cloud:** $0-14/month
- **Modal:** $0-5/month
- **Claude API:** ~$0.001 per proposal

**Total typical:** $0-10/month

---

## 🆘 Quick Fixes

| Problem | Fix |
|---------|-----|
| Streamlit won't start | `pip install -r requirements.txt` |
| ChromeDriver error | Use manual description fallback |
| Can't copy to clipboard | Manual copy from screen works |
| API rate limit | Wait 5 min, try again |
| Modal secret error | `modal secret list` to verify |

---

## 📱 Access from Phone

**Local (home WiFi):**
1. Get your Mac IP: System Settings → Network
2. On phone: `http://192.168.1.100:8501` (your IP)

**Cloud:**
- Just visit the Streamlit URL
- Works anywhere, any network

---

## ✅ You Have

✓ Proposal generator
✓ Local + cloud options
✓ Your voice built in
✓ Mobile-friendly
✓ 24/7 deployment ready
✓ $0-10/month cost

---

## 🚀 Start Now

**Try it:**
```bash
streamlit run execution/streamlit_proposal_app.py
```

**Deploy it:**
```bash
bash deploy.sh
```

---

**Everything documented.** Check [README_PROPOSAL_GENERATOR.md](README_PROPOSAL_GENERATOR.md) for full details.
