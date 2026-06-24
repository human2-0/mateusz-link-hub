# Mateusz link hub

Independent project landing page and shared path router for the services on
`79.72.79.130:8080`.

The root page is intentionally static. Application deployments own only their
private service ports; this repository owns `/` and the public route map:

- `/master-compounder/` → interactive CV static build
- `/thoughts-blog/` → Thoughts Blog service on `127.0.0.1:8082`
- `/tofufu/` → Tofufu service on `127.0.0.1:8083`

Run the small source checks with `python3 -m unittest discover -s tests`.
Production deployment is handled by `.github/workflows/deploy-oracle.yml`.
