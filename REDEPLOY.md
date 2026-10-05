# Redeploying the Final Build

Everything since Day 4 (RAG reindex automation, voice input/output,
unanswered-question logging, UI polish, expanded demo data, the Dr. Sharma
matching fix) needs to be pushed to GitHub and pulled onto your EC2
instance - it is not live yet just because it's built here.

## 1. Get the final code onto GitHub (from your Windows machine)

```powershell
cd $env:USERPROFILE\Downloads\symposium_day6   # or wherever the latest extract is
git init
git add -A
git commit -m "Days 5-8: RAG reindex, voice, unanswered-question logging, UI polish, expanded demo data, speaker-match fix"
git branch -M main
git remote add origin https://github.com/riteshchandru123-art/symposium.git
git push -u origin main --force
```

## 2. Pull it onto EC2

SSH in:
```powershell
ssh -i symposium-key.pem ubuntu@<your-instance-ip>
```
Then:
```bash
cd ~/symposium
git pull
```

## 3. Rebuild the containers with the new code

```bash
sudo docker compose -f docker-compose.prod.yml up --build -d
```

## 4. Apply the new migration (UnansweredQuestion model)

```bash
sudo docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

## 5. Re-seed with the expanded demo data

```bash
sudo docker compose -f docker-compose.prod.yml exec web python manage.py seed_data
```

## 6. Build the RAG index (needed for parking/wifi/dress-code questions to work)

```bash
sudo docker compose -f docker-compose.prod.yml exec web python -c "from rag.build_index import build_index; build_index()"
```
This needs real internet access to download the embedding model on first
run - your EC2 instance has it, unlike the sandbox this was built in, so
this should complete successfully (may take a minute or two the first time).

## 7. Verify live

```
http://<your-instance-ip>:8000
```
Run through the questions in `DEMO_SCRIPT.md` against this real URL, not
just localhost - confirm the parking/wifi question now gives a real answer
instead of "I couldn't find that" (that would mean step 6 didn't complete).

## 8. If you want voice input working on the live demo

Voice input needs HTTPS or localhost - plain `http://<ip>:8000` will
likely block microphone access. Voice output (spoken replies) has no such
restriction and will work as-is. Setting up HTTPS (e.g. via a free domain
+ Let's Encrypt, or an AWS Application Load Balancer with a certificate)
is a separate task - let me know if you want it built before demo day.
