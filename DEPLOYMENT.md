# Mateusz Apps deployment contract

The Oracle VM is one host for independent apps, not a Thoughts Blog server.
The `mateusz-link-hub` repository owns shared ingress and the public route map;
each app repository owns only its build and private runtime.

## Canonical names

Use kebab-case for every deployment-facing identifier. Dart package names may
keep snake_case because those are source identifiers, not infrastructure.

| App | Public path | VM runtime | Owner repository |
| --- | --- | --- | --- |
| Hub | `/` | `mateusz-apps-hub.service` | `mateusz-link-hub` |
| Thoughts Blog | `/thoughts-blog/` | `mateusz-thoughts-blog` | `thoughts_blog` |
| CV / Master Compounder | `/master-compounder/` | static files | `master_compounder` |
| Tofufu | `/tofufu/` | `mateusz-tofufu` | `tofufu` |
| Tofufu Mumble | port `64738` | `mateusz-tofufu-mumble.service` | `tofufu` |

Host paths are namespaced below `/opt/mateusz-apps/<app>/`. Persistent Tofufu
state remains below `/var/lib/pantofufu-*` for now; renaming state is a separate
data migration and must not be coupled to a routine application deploy.

The existing Oracle VCN (`thoughts_blog`) and subnet (`thoughts-subnet`) are
legacy cloud display names. They do not control deployment or routing. Rename
them to `mateusz-apps` / `mateusz-apps-subnet` in OCI when console or API access
is available; recreating the network is neither required nor desirable.

## Shared variables

All repositories use the same meanings and GitHub variable names:

- `ORACLE_HOST`: VM address.
- `ORACLE_USER`: SSH account, default `opc`.
- `ORACLE_SSH_PORT`: SSH port, default `22`.
- `PUBLIC_PORT`: private HTTP ingress port behind nginx, default `8080`.
- `THOUGHTS_PORT`: Thoughts Blog loopback port, default `8082`.
- `TOFUFU_PORT`: Tofufu loopback port, default `8083`.

`ORACLE_PORT` is retired because it previously meant SSH in one repository and
HTTP ingress in another. `ORACLE_DEPLOY_PATH` is retired; canonical paths are
part of this contract rather than per-repository secrets.

Local tooling uses `~/.ssh/oracle-mateusz-apps.key`. Scripts temporarily accept
the old `oracle-thoughts-blog.key` path to avoid breaking another workstation.

## Ownership rules

- The hub owns nginx/shared TLS, the root page, route definitions, and router.
- App deploys must not replace or restart shared ingress.
- Runtime ports bind to `127.0.0.1`; only nginx ports `80/443` and Mumble port
  `64738` are public.
- Images are immutable SHA tags. `latest` may be published, but a web runtime
  deploy uses the SHA tag that the workflow built.
- A workflow smoke-tests its private listener first and its public path second.
- Legacy `/master_compounder/` redirects to `/master-compounder/`.

## Adding another app

1. Choose one kebab-case app id and public path.
2. Assign a loopback-only port and `/opt/mateusz-apps/<app>/` directory.
3. Add the route and health check to the hub repository.
4. Give the app an independent workflow using the shared variables above.
5. Add its card to the hub only after its public smoke test passes.
