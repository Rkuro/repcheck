# Usage

The server systemd configuration is already setup - just do
```bash
systemctl restart repcheck
```

Configuration lives at `/etc/systemd/system/repcheck.service`

or just

```bash
systemctl show repcheck -p FragmentPath
```