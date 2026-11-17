# Deploying the Samarasyam 2026 portal

**Address:** https://iitrpr.ac.in/national-wellbeing-conclave-2026/

This runbook is for the seniors and IT staff who run the server. It assumes no web-development background.

## How it works

```
visitor → nginx on iitrpr.ac.in → python3 server.py (port 8100, this machine) → files in site/
```

- `build_site.py` reads `content/content.en.json` and writes the finished pages into `site/`.
- `server.py` sends visitors files from `site/` and **nothing else**. The repository, `.git`, the Python files and `content/` cannot be downloaded.
- There is no database, no login, no API and no stored user input. Feedback goes through a Google Form link.
- Both scripts use only Python's standard library (Python 3.8 or newer). Nothing needs to be installed with `pip`.

The examples below assume the repository lives at `/srv/nwc-26`. If it lives somewhere else, change the path in these commands and in `deploy/nwc.service`.

## 1. First-time setup (once, as root or with sudo)

```sh
python3 --version                                    # must be 3.8 or newer
useradd --system --create-home --shell /usr/sbin/nologin nwc
git clone https://github.com/singhgnoor/nwc-26.git /srv/nwc-26
chown -R nwc:nwc /srv/nwc-26
sudo -u nwc sh -c 'cd /srv/nwc-26 && python3 build_site.py'   # creates site/
sudo -u nwc sh -c 'cd /srv/nwc-26 && python3 -m unittest'     # all tests must pass
```

If the repository is private, give the `nwc` user a read-only deploy key on GitHub. Never put a personal token on the server.

Start the server as a service:

```sh
cp /srv/nwc-26/deploy/nwc.service /etc/systemd/system/nwc.service
systemctl daemon-reload
systemctl enable --now nwc
curl -I http://127.0.0.1:8100/national-wellbeing-conclave-2026/   # expect HTTP/1.0 200 OK
```

Give IT the snippet in `deploy/nginx-location.conf`. They add it to the iitrpr.ac.in nginx config and reload nginx. Then check from any machine:

```sh
curl -I https://iitrpr.ac.in/national-wellbeing-conclave-2026/
curl -I https://iitrpr.ac.in/national-wellbeing-conclave-2026/healthz
curl -I https://iitrpr.ac.in/national-wellbeing-conclave-2026/.git/HEAD     # must be 404
curl -I https://iitrpr.ac.in/national-wellbeing-conclave-2026/server.py     # must be 404
```

**No systemd access?** Use the `@reboot` crontab line at the bottom of `deploy/nwc.service`. It starts the server after a reboot, but it won't restart the server if it crashes.

## 2. Updating content (speakers, timings, photos, feedback link)

1. Edit `content/content.en.json` on your own computer.
2. Run `python3 build_site.py`. It lists every problem it finds; fix them until it says "Built".
3. Commit and push.
4. On the server, run:

   ```sh
   sudo -u nwc sh /srv/nwc-26/deploy/update.sh
   ```

That's all. If the build fails, the live site stays exactly as it was. You don't need to restart anything unless `server.py` changed, and `update.sh` tells you when it has.

To preview unconfirmed speakers on your own computer, run `python3 build_site.py --include-unconfirmed`. This writes to `site-preview/`, never to `site/`, and every page carries a PREVIEW banner. To look at it, run `NWC_SITE_DIR=site-preview python3 server.py`. **Never run this on the server.**

## 3. Checking that it is up

```sh
curl -I https://iitrpr.ac.in/national-wellbeing-conclave-2026/healthz   # 200 = up
systemctl status nwc
```

Add `https://iitrpr.ac.in/national-wellbeing-conclave-2026/healthz` to a free uptime monitor such as UptimeRobot (5-minute checks, email alerts to the organising team).

## 4. Reading the logs

```sh
journalctl -u nwc -f              # live
journalctl -u nwc --since today   # today's requests and errors
```

Each request is one line: the visitor's address, the method and path, the status, the bytes sent and the time taken.

## 5. Rolling back a bad update

The quickest way is to undo the change in git on your own computer and push it:

```sh
git revert <bad-commit>   # then push, then run update.sh on the server as usual
```

For an emergency on the server itself:

```sh
cd /srv/nwc-26
sudo -u nwc git log --oneline -5            # find the last good commit
sudo -u nwc git checkout <good-commit>
sudo -u nwc python3 build_site.py
```

This leaves the repository on a detached commit, so `update.sh` will refuse to pull. When the fix is pushed, go back with `sudo -u nwc git checkout main`, then run `update.sh`.

## 6. Fallback mirror on GitHub Pages

If the college server is down, the same `site/` folder can be served from GitHub Pages. All links are relative, so nothing needs to change.

- Use a **separate public repository** that contains only the built site, e.g. `nwc-26-mirror`. Do **not** turn on Pages for this repository: that would make the planning notes and source public.
- To publish, build locally, copy everything inside `site/` to the mirror repository's root, add an empty file named `.nojekyll`, commit and push. Then turn on Pages (Settings → Pages → Deploy from branch → `main` / root).
- GitHub Pages can't send the security headers that `server.py` adds, and clean URLs work slightly differently there. Treat the mirror as a short-term fallback.
- Keep the mirror's URL ready to send to the Dean's office if the main address goes down during the event.

## 7. Settings (environment variables)

| Variable | Default | Meaning |
|---|---|---|
| `NWC_HOST` | `127.0.0.1` | Address to listen on. Keep it local unless nginx is on another machine. |
| `NWC_PORT` | `8100` | Port (Zeitgeist uses 8000). |
| `NWC_SITE_DIR` | `<repo>/site` | The folder that is served. |
| `NWC_PREFIXES` | `/national-wellbeing-conclave-2026` | Comma-separated URL prefixes, e.g. add `/national-wellbeing-conclave-2026-staging`. |

## 8. Troubleshooting

| Symptom | Check |
|---|---|
| 502 Bad Gateway from nginx | `systemctl status nwc`; is it listening on the port nginx expects? |
| Service keeps restarting | `journalctl -u nwc -n 50`. "has no index.html" means you need to run `build_site.py`. |
| Change not visible | Did `update.sh` say "Built"? HTML is never cached, so a refresh shows it. CSS/JS URLs change with every build. |
| `update.sh` says "Not possible to fast-forward" | Someone edited files on the server. Don't edit there: `sudo -u nwc git status`, then discard local edits. |
