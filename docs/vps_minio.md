# MinIO Administration on VPS

MinIO Console is **not publicly exposed** on the VPS. Access is only possible via SSH tunnel.

## Prerequisites

- SSH access to the VPS: `rob@x.x.x.x`
- MinIO port `9001` is bound to `127.0.0.1` on the VPS (not reachable from the internet)

## Open SSH Tunnel

**Option A: Visible in terminal (recommended)**

```bash
ssh -L 19001:127.0.0.1:9001 -N rob@songprod.thwelly.ch
```

Terminal stays open with no prompt. Close with `Ctrl+C`.

**Option B: Background process**

```bash
ssh -L 19001:127.0.0.1:9001 -N -f rob@songprod.thwelly.ch
```

Runs silently in background.

## Access MinIO Console

Open in browser: http://localhost:19001

Credentials are in `/opt/chmusicpro/.env` on the VPS (`MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD`).

## Close Background Tunnel

```bash
kill $(pgrep -f "ssh -L 19001")
```

## Why Port 19001?

Port `9001` is already used by the local MinIO (Docker development environment). Port `19001` avoids the conflict.

## Bucket Setup

On first deployment, create the required buckets via MinIO Console:

1. Open http://localhost:19001
2. Go to **Buckets** > **Create Bucket**
3. Create: `chmusicpro-images`, `chmusicpro-songs`, `chmusicpro-projects`
