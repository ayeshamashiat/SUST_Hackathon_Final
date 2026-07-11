# SonarQube & CI Code Analysis

> v1 - written when SonarQube/CI support was first added. Update this file
> whenever the SonarQube setup or the CI workflow changes.

This project uses SonarQube-family code analysis in two places, for two
different jobs:

| | Where it runs | When | Persists history? |
|---|---|---|---|
| **Local SonarQube** (Docker) | Your own machine | Whenever you run it manually | Yes, on your machine |
| **SonarCloud** (via GitHub Actions) | GitHub's cloud runners | Automatically, every push/PR | Yes, on sonarcloud.io |

They are independent - scanning locally does not update the SonarCloud
dashboard, and vice versa. Local is for poking around while you write code;
SonarCloud is the "analyze every commit" pipeline.

## Why two separate targets? (the short version)

GitHub Actions runs your CI on a temporary cloud machine that has no
network path to a Docker container on your laptop - it cannot reach
`localhost:9000` on your machine. SonarCloud is a hosted version of
SonarQube that the cloud machine *can* reach, so that's what CI talks to.
The local Docker SonarQube is there because the requirements asked for it
explicitly, and it's genuinely useful for scanning before you even push.

## Running SonarQube locally

```bash
docker compose -f sonarqube/docker-compose.yml up -d
```

First startup takes 1-3 minutes (it's booting a small database + an
Elasticsearch-backed Java server). Watch it come up with:

```bash
docker compose -f sonarqube/docker-compose.yml logs -f sonarqube
```

Once ready, open **http://localhost:9000** - default login is `admin` /
`admin`, and it will immediately ask you to set a new password.

To actually scan this codebase against your local instance, generate a
token in the SonarQube UI (**My Account → Security → Generate Token**),
then run the scanner as a one-off container from the repo root:

```bash
docker run --rm \
  --network sonarqube_default \
  -e SONAR_HOST_URL=http://sonarqube:9000 \
  -e SONAR_TOKEN=<paste your local token> \
  -v "$(pwd):/usr/src" \
  sonarsource/sonar-scanner-cli
```

Stop it with `docker compose -f sonarqube/docker-compose.yml down` (add `-v`
to also wipe the local SonarQube database - that only deletes your local
scan history, never your actual source code).

### Common local issue: Elasticsearch fails to start

If the `sonarqube` container logs show something like *"max virtual memory
areas vm.max_map_count [65530] is too low"*, your host's kernel setting
needs raising (one-time, requires sudo, changes host config outside this
project - ask before running this if someone else set up the machine):

```bash
sudo sysctl -w vm.max_map_count=262144
```

This repo's dev container already had `vm.max_map_count=1048576` (well
above the minimum), so this usually won't come up.

## Setting up SonarCloud (one-time, required before CI will pass)

CI is already wired up (`.github/workflows/sonarcloud.yml`), but it needs
two things from you that I can't create on your behalf (they require your
own accounts/credentials):

1. **Create a SonarCloud account and project**
   - Go to [sonarcloud.io](https://sonarcloud.io) → sign in with your GitHub
     account → "+" → "Analyze new project" → pick this repository
     (`ayeshamashiat/SUST_Hackathon_Final`).
   - Note the **Organization Key** and **Project Key** it assigns you.

2. **Update `sonar-project.properties`** (repo root) with those real values:
   ```properties
   sonar.projectKey=<your real project key>
   sonar.organization=<your real organization key>
   ```
   (Placeholders are currently `sust-hackathon-super-agent` / `CHANGE_ME_your_sonarcloud_org`.)

3. **Generate a token**: SonarCloud → your avatar → **My Account** →
   **Security** → **Generate Token**. Copy it immediately (shown once).

4. **Add it as a GitHub secret**: on GitHub, go to this repo →
   **Settings** → **Secrets and variables** → **Actions** →
   **New repository secret** → name it exactly `SONAR_TOKEN` → paste the
   token value.

Once all four steps are done, the next push (or re-run of the failed
workflow run) will succeed and start populating the SonarCloud dashboard.

## What the CI workflow actually does

`.github/workflows/sonarcloud.yml` triggers on every push to any branch and
every pull request. Each run:

1. GitHub allocates a temporary Ubuntu VM.
2. Checks out this repo's full git history (SonarCloud needs it to compute
   which lines are "new code" vs. old, for new-code-only quality gates).
3. Runs the official `SonarSource/sonarqube-scan-action`, which downloads
   the scanner, reads `sonar-project.properties`, and uploads the analysis
   to SonarCloud using the `SONAR_TOKEN` secret.
4. SonarCloud computes the Quality Gate result and, on pull requests, posts
   a summary comment directly on the PR.

Nothing is deployed anywhere - this is analysis only (CI), not CD. The VM
and everything on it is destroyed when the job finishes; only the analysis
result sent to SonarCloud persists.

## Troubleshooting

**Workflow run fails with an authentication error** - `SONAR_TOKEN` secret
is missing, misspelled, or the token was regenerated/revoked on SonarCloud
since it was added to GitHub. Regenerate and re-add it.

**Workflow fails with "project not found" / key mismatch** - the
`sonar.projectKey`/`sonar.organization` values in `sonar-project.properties`
don't match what SonarCloud actually assigned your project. Copy them
exactly from the SonarCloud project's **Administration → General Settings**
page.

**Local scan complains about network** - the one-off scanner container
above must be on the same Docker network as the local SonarQube server
(`sonarqube_default`, from the compose project name) - confirm with
`docker network ls` if it's been renamed.
