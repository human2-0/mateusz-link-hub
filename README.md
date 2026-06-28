# Mateusz link hub

Independent landing page and route gateway for Mateusz Apps on Oracle.

The root page is intentionally static. Application deployments own only their
private service ports; this repository owns `/` and the public route map:

- `/master-compounder/` → interactive CV static build
- `/thoughts-blog/` → Thoughts Blog service on `127.0.0.1:8082`
- `/tofufu/` → Tofufu service on `127.0.0.1:8083`

Run the small source checks with `python3 -m unittest discover -s tests`.
Production deployment is handled by `.github/workflows/deploy-oracle.yml`.
The VM naming contract, ownership boundaries, and expansion checklist are in
[`DEPLOYMENT.md`](DEPLOYMENT.md).
