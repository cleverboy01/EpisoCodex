---
name: deploy
description: Deploy the project to a target environment (staging, production, etc.)
when_to_use: Use when user says deploy, ship, release, push to production, go live
short_description: Deploy to environment
argument_hint: environment (staging | production | dev)
allowed_tools: [run_terminal_cmd, read_file, list_dir, grep]
user_invocable: true
disable_model_invocation: false
enabled: true
---

# Deploy Skill

Safely deploys the project to the target environment with pre-flight checks.

## Pre-flight Checks
1. Confirm target environment (default: staging if not specified)
2. Check for uncommitted changes: `git status`
3. Verify on the correct branch (main/master for production)
4. Run tests: detect and run project test command
5. Build if needed: detect build system (npm build, cargo build, etc.)

## Deployment Steps
1. **Tag/version** (for production): check if a release tag is needed
2. **Deploy** using the project's deploy method:
   - Docker: `docker build && docker push && kubectl apply`
   - Heroku: `git push heroku main`
   - Vercel/Netlify: `vercel --prod` or platform CLI
   - Custom: look for `deploy.sh`, `Makefile deploy`, `scripts/deploy`
3. **Verify**: check deployment status (health check endpoint, logs)
4. **Report**: deployment URL, version, environment

## Safety Rules
- NEVER deploy directly to production without explicit user confirmation
- ALWAYS run tests before deploying
- ALWAYS check for uncommitted work (user may not want to deploy it)
- If deploy fails: preserve error logs and report clearly
