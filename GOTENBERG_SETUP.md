# Gotenberg Setup Guide

This auto-print service uses [Gotenberg](https://gotenberg.dev/) for high-quality DOCX to PDF conversion.

## What is Gotenberg?

Gotenberg is a Docker-powered stateless API for converting various document formats to PDF. It uses LibreOffice under the hood, providing much cleaner and more accurate PDF conversions compared to command-line tools like Pandoc.

## Prerequisites

- **Docker Desktop for Windows**: Download and install from [docker.com](https://www.docker.com/products/docker-desktop/)
  - Make sure Docker Desktop is running before starting the auto-print service

## Quick Start

### 1. Start Gotenberg Container

Open PowerShell or Command Prompt and run:

```powershell
docker run -d -p 3000:3000 --name gotenberg --restart unless-stopped gotenberg/gotenberg:8
```

**Command breakdown:**
- `-d` - Run in detached mode (background)
- `-p 3000:3000` - Map port 3000 from container to host
- `--name gotenberg` - Name the container for easy management
- `--restart unless-stopped` - Auto-restart container if Docker restarts
- `gotenberg/gotenberg:8` - Use Gotenberg version 8

### 2. Verify Gotenberg is Running

Check the container status:

```powershell
docker ps
```

You should see the `gotenberg` container listed and running.

Test the health endpoint:

```powershell
curl http://localhost:3000/health
```

Or open in browser: http://localhost:3000/health

You should receive a `200 OK` response.

## Configuration

The auto-print service is configured to connect to Gotenberg at `http://localhost:3000` by default.

To change this, edit `config/config.json`:

```json
{
  "gotenberg": {
    "url": "http://localhost:3000",
    "timeout": 30
  }
}
```

## Managing the Container

### Stop Gotenberg
```powershell
docker stop gotenberg
```

### Start Gotenberg
```powershell
docker start gotenberg
```

### Restart Gotenberg
```powershell
docker restart gotenberg
```

### View Logs
```powershell
docker logs gotenberg
```

### Remove Container
```powershell
docker stop gotenberg
docker rm gotenberg
```

## Troubleshooting

### Container won't start
- Make sure Docker Desktop is running
- Check if port 3000 is already in use: `netstat -ano | findstr :3000`
- Try a different port: `docker run -d -p 3001:3000 --name gotenberg gotenberg/gotenberg:8`
  - Update `config.json` to use `http://localhost:3001`

### Conversion fails
- Check Gotenberg container is running: `docker ps`
- Check Gotenberg logs: `docker logs gotenberg`
- Verify connectivity: `curl http://localhost:3000/health`

### Auto-print service can't connect
- Ensure the URL in `config.json` matches your Gotenberg container
- Check Windows Firewall isn't blocking localhost connections
- Restart the auto-print service after starting Gotenberg

## Performance Notes

- First conversion may be slower (~2-3 seconds) as LibreOffice initializes
- Subsequent conversions are much faster (~0.5-1 second)
- The container uses minimal resources when idle
- Memory usage: ~200-300 MB

## Advanced Configuration

### Custom Port Mapping
```powershell
docker run -d -p 8080:3000 --name gotenberg gotenberg/gotenberg:8
```
Then update `config.json`:
```json
{
  "gotenberg": {
    "url": "http://localhost:8080"
  }
}
```

### Resource Limits
```powershell
docker run -d -p 3000:3000 --name gotenberg --memory="512m" --cpus="1.0" gotenberg/gotenberg:8
```

### Update to Latest Version
```powershell
docker stop gotenberg
docker rm gotenberg
docker pull gotenberg/gotenberg:8
docker run -d -p 3000:3000 --name gotenberg --restart unless-stopped gotenberg/gotenberg:8
```

## References

- [Gotenberg Official Documentation](https://gotenberg.dev/)
- [Gotenberg GitHub Repository](https://github.com/gotenberg/gotenberg)
- [Docker Desktop Documentation](https://docs.docker.com/desktop/)
