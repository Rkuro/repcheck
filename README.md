# Usage

The server systemd configuration is already setup - just do
```bash
git pull
systemctl restart repcheck
```

Configuration lives at `/etc/systemd/system/repcheck.service`

or just

```bash
systemctl show repcheck -p FragmentPath
```

## Configuration

Need to set these on-server (don't check into git obv)
```bash
# .env
PLURAL_API_KEY = "abcdef"
POSTGRES_DB_PASSWORD = "abcdef"
```


## Local Dev
```bash
uvicorn app.main:app --reload
```