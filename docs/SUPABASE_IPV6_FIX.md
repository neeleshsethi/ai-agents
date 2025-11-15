# Fixing Supabase PostgreSQL Connection in Docker with IPv6

## Problem Overview

When connecting a Dockerized application to Supabase PostgreSQL database, you may encounter connection errors like:

```
psycopg.OperationalError: [Errno -5] No address associated with hostname
```

or

```
FATAL: Tenant or user not found
```

**Root Cause**: Supabase's direct database endpoints (`db.{project-ref}.supabase.co`) use **IPv6 addresses only**. Docker on macOS (via Colima) and many Docker setups don't have IPv6 routing enabled by default, preventing containers from connecting to IPv6-only services.

## Solution Summary

1. Configure Docker daemon (Colima) to enable IPv6
2. Update docker-compose.yml to use IPv6 networking
3. Use correct Supabase connection string format
4. Ensure application passes required thread_id parameter

---

## Detailed Step-by-Step Fix

### Step 1: Configure Colima Docker Daemon for IPv6

**Location**: Create/edit the daemon configuration file

**For Colima on macOS**:
```bash
~/.colima/default/daemon/daemon.json
```

**For Docker Desktop on macOS**:
```bash
~/Library/Containers/com.docker.docker/Data/docker-daemon.json
```

**For Linux**:
```bash
/etc/docker/daemon.json
```

**For Windows**:
```bash
%ProgramData%\Docker\config\daemon.json
```

**File Contents**:
```json
{
  "ipv6": true,
  "fixed-cidr-v6": "fd00:ffff::/80",
  "ip6tables": true,
  "experimental": true
}
```

**Explanation**:
- `"ipv6": true` - Enables IPv6 support in Docker
- `"fixed-cidr-v6"` - Defines the IPv6 subnet range for container addresses
- `"ip6tables": true` - Enables Docker to configure firewall rules for IPv6
- `"experimental": true` - May be required for some Docker versions

**Apply Changes**:

For Colima:
```bash
colima stop
colima start
```

For Docker Desktop:
- Go to Settings → Docker Engine
- Add/merge the configuration
- Click "Apply & Restart"

For Linux:
```bash
sudo systemctl restart docker
```

### Step 2: Verify IPv6 is Working

Test that Docker can use IPv6:

```bash
# Create a test IPv6 network
docker network create --ipv6 --subnet fd00:ffff::/80 ip6net

# Test IPv6 connectivity
docker run --rm -it --network ip6net busybox ping6 google.com -c3

# Clean up
docker network rm ip6net
```

If you receive successful ping replies, IPv6 is working.

### Step 3: Update docker-compose.yml

Add IPv6 network configuration to your `docker-compose.yml`:

```yaml
networks:
  default:
    enable_ipv6: true
    ipam:
      config:
        - subnet: fd00:c16a:601e::/80
          gateway: fd00:c16a:601e::1

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.fastapi
    ports:
      - 8000:8000
    env_file:
      - .env
    restart: unless-stopped
    volumes:
      - ./src/api:/app/src/api

  streamlit-app:
    build:
      context: .
      dockerfile: Dockerfile.streamlit
    ports:
      - 8501:8501
    environment:
      - FASTAPI_URL=http://api:8000
    env_file:
      - .env
    restart: unless-stopped
    volumes:
      - ./src/chatbot-ui:/app/src/chatbot-ui
    depends_on:
      - api
```

**Key Changes**:
- Added `networks` section at the top level
- Configured `enable_ipv6: true`
- Specified IPv6 subnet and gateway

### Step 4: Configure Supabase Connection String

**Get your Supabase connection details from Dashboard**:
1. Go to Supabase Dashboard → Your Project → Settings → Database
2. Find your connection string

**Correct Connection String Format**:

```bash
# In your .env file
SUPABASE_DB_URL="postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_REF.supabase.co:5432/postgres"
```

**Important Notes**:
- Username is just `postgres` (NOT `postgres.{project-ref}`)
- Hostname is `db.{project-ref}.supabase.co`
- Port is `5432` (direct connection)
- Do NOT use the pooler endpoints for LangGraph checkpointing

**Example**:
```bash
SUPABASE_DB_URL="postgresql://postgres:Commercial$123@db.hmmmhqszkluuypmrndxw.supabase.co:5432/postgres"
```

### Step 5: Verify DNS Resolution

Test that the hostname resolves to IPv6:

```bash
# From host machine
host db.YOUR_PROJECT_REF.supabase.co

# Should return something like:
# db.YOUR_PROJECT_REF.supabase.co has IPv6 address 2406:da1c:f42:ae02:3468:ddd3:28b6:bde3
```

Test from inside Docker container:

```bash
docker exec YOUR_CONTAINER python -c "import socket; print(socket.getaddrinfo('db.YOUR_PROJECT_REF.supabase.co', 5432, socket.AF_INET6))"
```

### Step 6: Rebuild and Restart Containers

```bash
cd /path/to/your/project

# Stop and remove existing containers
docker compose down -v

# Rebuild and start with new configuration
docker compose up -d --build
```

### Step 7: Application Code Requirements

**Ensure thread_id is mandatory**:

In your Pydantic models (`models.py`):

```python
from pydantic import BaseModel, Field
from typing import List

class AgentRequest(BaseModel):
    query: str = Field(..., description="The query to be used in the RAG pipeline")
    thread_id: str = Field(..., description="The thread ID for conversation continuity")  # REQUIRED, not Optional
```

**Generate and pass thread_id from frontend**:

In Streamlit app (`streamlit_app.py`):

```python
import streamlit as st
import uuid

def get_session_id():
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    return st.session_state.session_id

session_id = get_session_id()

# When making API call
api_call("post", f"{config.API_URL}/rag", json={
    "query": prompt,
    "thread_id": session_id
})
```

**Use correct config access in LangGraph**:

In your graph code (`graph.py`):

```python
from api.core.config import config as app_config

# In your run_agent function
with PostgresSaver.from_conn_string(app_config.SUPABASE_DB_URL) as checkpointer:
    checkpointer.setup()
    graph = workflow.compile(checkpointer=checkpointer)
    result = graph.invoke(initial_state, config=langgraph_config)
```

---

## Common Errors and Solutions

### Error: "No address associated with hostname"

**Cause**: Docker can't resolve IPv6 addresses
**Solution**: Follow Steps 1-3 to enable IPv6 in Docker

### Error: "Tenant or user not found"

**Cause**: Using pooler connection instead of direct connection, or wrong username format
**Solution**: Use direct connection format: `postgres:password@db.{ref}.supabase.co:5432/postgres`

### Error: "null value in column 'thread_id' violates not-null constraint"

**Cause**: Application not passing thread_id to the database
**Solution**: Make thread_id mandatory in your API model and ensure frontend passes it

### Error: "Network is unreachable"

**Cause**: IPv6 routing not properly configured
**Solution**: Verify daemon.json configuration and restart Docker/Colima

---

## Verification Checklist

- [ ] Created/updated daemon.json with IPv6 configuration
- [ ] Restarted Docker/Colima
- [ ] Verified IPv6 connectivity with test network
- [ ] Updated docker-compose.yml with IPv6 network settings
- [ ] Configured correct Supabase connection string in .env
- [ ] Verified DNS resolution returns IPv6 address
- [ ] Made thread_id mandatory in API models
- [ ] Frontend generates and passes thread_id
- [ ] Rebuilt containers with `docker compose up -d --build`
- [ ] Tested connection from inside container

---

## Testing the Connection

After applying all fixes, test the connection:

```bash
# Check containers are running
docker ps

# Check API logs for errors
docker logs ai-agents-api-1 --tail 50

# Test from inside container
docker exec ai-agents-api-1 python -c "
from langgraph.checkpoint.postgres import PostgresSaver
import os

# Test connection
conn_string = os.getenv('SUPABASE_DB_URL')
print(f'Testing connection to: {conn_string}')

with PostgresSaver.from_conn_string(conn_string) as checkpointer:
    checkpointer.setup()
    print('✓ Connection successful!')
    print('✓ Tables created/verified!')
"
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  Host Machine (macOS)                                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Colima VM with IPv6 Enabled                           │ │
│  │  ┌──────────────────┐  ┌──────────────────┐            │ │
│  │  │  Streamlit       │  │  FastAPI         │            │ │
│  │  │  Container       │→ │  Container       │            │ │
│  │  │  (IPv6 enabled)  │  │  (IPv6 enabled)  │            │ │
│  │  └──────────────────┘  └─────────┬────────┘            │ │
│  │                                   │                      │ │
│  │                          IPv6: fd00:c16a:601e::x        │ │
│  └───────────────────────────────────┼──────────────────────┘ │
│                                      │                        │
└──────────────────────────────────────┼────────────────────────┘
                                       │
                            IPv6 Route Enabled
                                       │
                                       ↓
                    ┌──────────────────────────────────┐
                    │  Supabase PostgreSQL              │
                    │  db.{ref}.supabase.co             │
                    │  IPv6: 2406:da1c:f42:...          │
                    └──────────────────────────────────┘
```

---

## References

- [Supabase IPv6 Blog Post](https://supabase.com/blog/ipv6-support)
- [Docker IPv6 Documentation](https://docs.docker.com/config/daemon/ipv6/)
- [LangGraph PostgreSQL Checkpointer](https://langchain-ai.github.io/langgraph/how-tos/persistence_postgres/)

---

## Summary

The key to fixing Supabase connection issues in Docker is understanding that:

1. **Supabase uses IPv6** for direct database connections
2. **Docker needs explicit IPv6 configuration** at both daemon and network levels
3. **Connection string format matters** - use direct connection, not pooler
4. **LangGraph requires thread_id** - must be non-null and passed from frontend

After implementing these fixes, your Dockerized application will successfully connect to Supabase PostgreSQL with full LangGraph checkpointing support.

---

**Last Updated**: November 2025
**Tested On**: macOS with Colima, Docker Desktop on macOS
**Supabase Version**: Current (as of Nov 2025)
**LangGraph Version**: 0.5.1+
