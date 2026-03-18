# Week 7 Assignment - Microservice with Discovery

## Student Info
- Name: Vandan Sanket Shah
- SID: 018521672

## Assignment Requirements
- Run 2 service instances
- Register with registry
- Client discovers service
- Client calls random instance

## Deliverables
- GitHub repo
- Architecture diagram: `docs/architecture.md`
- Demo video: https://drive.google.com/drive/folders/1QJDRMh_5WYUnxM-V8F6R3O_lDeHsvikq?usp=sharing

## How To Start Everything
1. Start Docker Desktop on macOS.
2. Run the full stack:

```bash
docker compose up --build
```

3. Open services:
- Consul UI: `http://localhost:8500`
- Service instance 1: `http://localhost:8001/hello`
- Service instance 2: `http://localhost:8002/hello`
- Discovery client: `http://localhost:9000`

4. Verify discovery and random routing:

```bash
curl http://localhost:9000/instances
curl http://localhost:9000/invoke
curl http://localhost:9000/invoke
curl http://localhost:9000/invoke
```

5. Stop everything:

```bash
docker compose down
```
