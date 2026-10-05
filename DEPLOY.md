# Day 4 — Deploying to AWS

Goal: a rough but real version of the app live at a public URL today, so
deployment problems surface now instead of on Day 8.

## 1. Launch the EC2 instance (AWS Console)

- Ubuntu 22.04 LTS AMI
- `t3.small` is enough for a demo (avoid `t2.micro` — sentence-transformers +
  gunicorn + postgres can be tight on 1GB RAM)
- Create or reuse a key pair for SSH
- **Security group**: allow inbound
  - TCP 22 (SSH) from your IP
  - TCP 8000 (the app) from anywhere (0.0.0.0/0) for the demo
- Launch it, note the public IP

## 2. Get the code onto the instance

```bash
ssh -i your-key.pem ubuntu@<instance-public-ip>
git clone <your-repo-url>
cd symposium
```

## 3. Configure environment

```bash
cp .env.example .env
nano .env
```
Set at minimum:
- `DJANGO_SECRET_KEY` — generate a real random string, don't leave the placeholder
- `DJANGO_ALLOWED_HOSTS` — set to `<instance-public-ip>` (and your domain later, if any)
- `DJANGO_DEBUG=False`
- `DB_PASSWORD` — a real password, not `symposium`
- Your LLM API key, once your partner's agent code needs it

## 4. Run the deploy script

```bash
chmod +x deploy_ec2.sh
./deploy_ec2.sh
```
This installs Docker if needed, builds the production containers
(`docker-compose.prod.yml` — gunicorn, not the dev server, `DEBUG=False`,
static files handled by WhiteNoise), and starts everything.

## 5. Verify it's actually live

From your own machine (not the instance):
```bash
curl http://<instance-public-ip>:8000/
```
Should return the chat page HTML. Also open it in a browser to confirm the
UI renders and a chat message round-trips correctly.

## 6. What's intentionally rough at this stage

- No domain name / HTTPS yet — plain HTTP on port 8000 is fine for an internal demo
- No nginx reverse proxy — gunicorn is directly exposed, which is fine at this scale
- Only one gunicorn instance — fine for a handful of concurrent users at a symposium demo

These are reasonable things to tighten later (Day 7 polish) if time allows,
not blockers for having something real and reachable today.

## Common failure points to check if it doesn't come up

- **Can't reach the app at all**: security group not allowing port 8000 inbound
- **"DisallowedHost" error**: `DJANGO_ALLOWED_HOSTS` in `.env` doesn't match
  the IP/domain you're visiting from
- **Static files look unstyled**: `collectstatic` didn't run — check
  `docker compose -f docker-compose.prod.yml logs web`
- **Database connection errors**: `db` container isn't healthy yet when `web`
  starts — the compose file's `depends_on: condition: service_healthy` should
  prevent this, but check `docker compose -f docker-compose.prod.yml ps`
