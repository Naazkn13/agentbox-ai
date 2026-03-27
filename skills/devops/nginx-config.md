---
id: nginx-config
name: Nginx Configuration Expert
category: deploying
level1: "For Nginx server blocks, reverse proxy, SSL/TLS, rate limiting, gzip, security headers"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 2
---

<!-- LEVEL 1 START -->
**Nginx Configuration Expert** — Activate for: Nginx config, server blocks, reverse proxy, proxy_pass, SSL/TLS termination, Let's Encrypt, rate limiting, gzip compression, security headers, load balancing, HTTP to HTTPS redirects, upstream configuration.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## Nginx Configuration Expert — Core Instructions

1. **Test every config change with `nginx -t` before reloading** — syntax errors will prevent reload and leave the running config unchanged, but a bad config after a full restart will take the server down.
2. **Use `location` specificity rules correctly** — exact match (`=`) beats prefix (`^~`) beats regex (`~`/`~*`) beats longest prefix; unexpected routing bugs are almost always a specificity mistake.
3. **Terminate SSL at Nginx, never pass raw HTTPS upstream** — use `proxy_pass http://` to your backend over internal network; only the Nginx-to-client leg should be HTTPS.
4. **Set `proxy_set_header` for every reverse-proxied backend** — at minimum: `Host`, `X-Real-IP`, `X-Forwarded-For`, and `X-Forwarded-Proto`; backends need these to construct correct URLs and log real IPs.
5. **Define rate limit zones in the `http` block, not `server` or `location`** — `limit_req_zone` is a declaration; `limit_req` is the enforcement; splitting them across includes is a common misconfiguration.
6. **Enable `gzip` only for compressible MIME types** — never gzip images, video, or already-compressed formats; always set `gzip_vary on` so CDNs cache the correct version.
7. **Reload with `nginx -s reload` (graceful), not restart** — reload drains active connections; restart drops them; use restart only when upgrading the Nginx binary itself.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## Nginx Configuration Expert — Full Reference

### Basic Server Block Structure

```nginx
# /etc/nginx/nginx.conf — http block globals
http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    sendfile      on;
    tcp_nopush    on;
    keepalive_timeout 65;

    # Include all site configs
    include /etc/nginx/conf.d/*.conf;
}
```

```nginx
# /etc/nginx/conf.d/myapp.conf
server {
    listen 80;
    server_name example.com www.example.com;

    root /var/www/myapp/public;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;   # SPA fallback
    }

    location /api/ {
        proxy_pass http://127.0.0.1:3000/;
    }
}
```

### HTTPS + Let's Encrypt (Certbot)

```bash
# Obtain certificate (Certbot manages renewal via systemd timer)
certbot certonly --nginx -d example.com -d www.example.com
```

```nginx
# HTTP → HTTPS redirect
server {
    listen 80;
    server_name example.com www.example.com;
    return 301 https://example.com$request_uri;
}

# www → non-www redirect (HTTPS)
server {
    listen 443 ssl http2;
    server_name www.example.com;

    ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    return 301 https://example.com$request_uri;
}

# Primary HTTPS server
server {
    listen 443 ssl http2;
    server_name example.com;

    ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    # Mozilla Modern TLS config
    ssl_protocols             TLSv1.2 TLSv1.3;
    ssl_ciphers               ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache         shared:SSL:10m;
    ssl_session_timeout       1d;
    ssl_stapling              on;
    ssl_stapling_verify       on;

    include /etc/nginx/snippets/security-headers.conf;
    include /etc/nginx/snippets/gzip.conf;

    location / {
        proxy_pass http://127.0.0.1:3000;
        include /etc/nginx/snippets/proxy-params.conf;
    }
}
```

### Reverse Proxy Params Snippet

```nginx
# /etc/nginx/snippets/proxy-params.conf
proxy_http_version      1.1;
proxy_set_header        Host              $host;
proxy_set_header        X-Real-IP         $remote_addr;
proxy_set_header        X-Forwarded-For   $proxy_add_x_forwarded_for;
proxy_set_header        X-Forwarded-Proto $scheme;
proxy_set_header        Upgrade           $http_upgrade;   # WebSocket support
proxy_set_header        Connection        "upgrade";
proxy_cache_bypass      $http_upgrade;
proxy_read_timeout      60s;
proxy_connect_timeout   10s;
proxy_send_timeout      60s;
proxy_buffer_size       4k;
proxy_buffers           8 16k;
```

### Load Balancing Upstream

```nginx
upstream app_servers {
    least_conn;   # or: round_robin (default), ip_hash, hash $request_uri

    server 10.0.1.10:3000 weight=3;
    server 10.0.1.11:3000 weight=1;
    server 10.0.1.12:3000 backup;      # only used when others are down

    keepalive 32;   # persistent connections to upstream
}

server {
    listen 443 ssl http2;
    server_name example.com;

    location / {
        proxy_pass http://app_servers;
        include /etc/nginx/snippets/proxy-params.conf;
    }
}
```

### Rate Limiting

```nginx
# http block — declare zones
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;

# server block — enforce
location /api/ {
    limit_req zone=api_limit burst=20 nodelay;
    limit_req_status 429;
    proxy_pass http://app_servers;
    include /etc/nginx/snippets/proxy-params.conf;
}

location /auth/login {
    limit_req zone=login_limit burst=3;
    limit_req_status 429;
    proxy_pass http://app_servers;
    include /etc/nginx/snippets/proxy-params.conf;
}
```

### Gzip Compression Snippet

```nginx
# /etc/nginx/snippets/gzip.conf
gzip              on;
gzip_vary         on;
gzip_proxied      any;
gzip_comp_level   5;
gzip_min_length   256;
gzip_types
    text/plain
    text/css
    text/javascript
    application/javascript
    application/json
    application/xml
    application/rss+xml
    application/atom+xml
    image/svg+xml
    font/woff2;
# Do NOT include: image/jpeg, image/png, image/webp, video/* — already compressed
```

### Security Headers Snippet

```nginx
# /etc/nginx/snippets/security-headers.conf
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
add_header X-Frame-Options            "DENY" always;
add_header X-Content-Type-Options     "nosniff" always;
add_header X-XSS-Protection           "1; mode=block" always;
add_header Referrer-Policy            "strict-origin-when-cross-origin" always;
add_header Permissions-Policy         "geolocation=(), microphone=(), camera=()" always;
add_header Content-Security-Policy
    "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self'; font-src 'self'; object-src 'none'; frame-ancestors 'none';"
    always;
```

### Cache Headers for Static Assets

```nginx
location ~* \.(js|css|woff2|woff|ttf|svg|ico)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    access_log off;
}

location ~* \.(png|jpg|jpeg|webp|gif)$ {
    expires 30d;
    add_header Cache-Control "public";
}
```

### Location Matching Reference

```nginx
# Exact match (highest priority)
location = /health { return 200 "OK"; }

# Case-sensitive regex
location ~ \.php$ { fastcgi_pass 127.0.0.1:9000; }

# Case-insensitive regex
location ~* \.(jpg|jpeg|png|gif)$ { expires 30d; }

# Prefix match, stops regex search (^~)
location ^~ /static/ { root /var/www; }

# Prefix match (lowest priority, fallback)
location / { try_files $uri $uri/ =404; }
```

### Common Redirects

```nginx
# HTTP → HTTPS
return 301 https://$host$request_uri;

# www → non-www
server_name www.example.com;
return 301 https://example.com$request_uri;

# Legacy path redirect
location /old-path {
    return 301 /new-path;
}

# Remove trailing slash
rewrite ^/(.*)/$ /$1 permanent;
```

### CLI Commands

```bash
nginx -t                    # test config syntax
nginx -s reload             # graceful reload (drains connections)
nginx -s quit               # graceful shutdown
nginx -V                    # show compiled-in modules and flags
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log

# Test SSL config with ssllabs or locally
openssl s_client -connect example.com:443 -servername example.com
```

### Anti-patterns to Avoid
- Using `proxy_pass` with a trailing slash inconsistently — `proxy_pass http://backend` strips nothing; `proxy_pass http://backend/` strips the `location` prefix; mixing these causes 404s
- Putting `limit_req_zone` inside a `server` or `location` block — it must be in the `http` block; Nginx will silently ignore it otherwise
- Setting `ssl_protocols TLSv1 TLSv1.1` — deprecated, insecure; minimum is TLSv1.2
- Forgetting `always` on `add_header` — without it, headers are only added on 2xx/3xx responses, missing error pages
- Gzipping already-compressed files (images, video) — wastes CPU and can slightly increase file size
- Not setting `proxy_read_timeout` — default is 60s but upstream long-poll endpoints will silently drop connections
<!-- LEVEL 3 END -->
