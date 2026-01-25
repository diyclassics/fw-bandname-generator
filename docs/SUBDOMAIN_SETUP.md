# Subdomain Configuration Guide

How to set up a subdomain (like `fwbng.exploratoryphilology.org`) to point to your DigitalOcean droplet while keeping your main domain on GitHub Pages.

---

## How It Works

```
exploratoryphilology.org     → GitHub Pages (unchanged)
fwbng.exploratoryphilology.org → DigitalOcean Droplet (new)
```

Each subdomain can point to a completely different server. They're independent.

---

## Step 1: Find Your DNS Settings

Your DNS is managed wherever you registered your domain or wherever you've pointed your nameservers.

### Common registrars:

| Registrar | DNS Settings Location |
|-----------|----------------------|
| Namecheap | Domain List > Manage > Advanced DNS |
| GoDaddy | My Products > DNS |
| Google Domains | My Domains > DNS |
| Cloudflare | Select domain > DNS |
| Hover | Control Panel > DNS |
| Porkbun | Domain Management > DNS |

### Check your nameservers

Your domain might use:
- **Registrar's DNS** (default)
- **Cloudflare** (if you set it up for CDN/security)
- **Custom nameservers**

To find out, use:
```bash
dig NS exploratoryphilology.org +short
```

Or use [whatsmydns.net](https://www.whatsmydns.net/) and search for NS records.

---

## Step 2: Add the A Record

In your DNS management panel:

1. **Add a new record**
2. **Fill in the fields:**

| Field | Value |
|-------|-------|
| **Type** | A |
| **Name** / **Host** | `fwbng` (just the subdomain part) |
| **Value** / **Points to** | `YOUR_DROPLET_IP` (e.g., `203.0.113.10`) |
| **TTL** | 3600 (or "1 Hour" or "Automatic") |

3. **Save**

### Examples by registrar:

**Namecheap:**
```
Type: A Record
Host: fwbng
Value: 203.0.113.10
TTL: Automatic
```

**Cloudflare:**
```
Type: A
Name: fwbng
IPv4 address: 203.0.113.10
Proxy status: DNS only (gray cloud) - for initial setup
TTL: Auto
```

**GoDaddy:**
```
Type: A
Name: fwbng
Value: 203.0.113.10
TTL: 1 Hour
```

---

## Step 3: Verify DNS Propagation

DNS changes can take 5 minutes to 48 hours to propagate worldwide (usually faster).

### Check from command line:

```bash
dig fwbng.exploratoryphilology.org +short
```

Should return your droplet's IP address.

### Check online:

Use [whatsmydns.net](https://www.whatsmydns.net/):
1. Enter `fwbng.exploratoryphilology.org`
2. Select **A** record type
3. Click Search
4. Green checkmarks mean it's propagated to that location

### Check if it reaches your server:

```bash
curl -I http://fwbng.exploratoryphilology.org
```

If nginx is running on your droplet, you should see a response.

---

## Step 4: Verify Main Domain Unchanged

Your GitHub Pages site should still work:

```bash
curl -I https://exploratoryphilology.org
```

The main domain and subdomain are completely independent.

---

## Common Configurations

### Multiple subdomains to same droplet

Add multiple A records, all pointing to the same IP:

| Name | Type | Value |
|------|------|-------|
| fwbng | A | 203.0.113.10 |
| blog | A | 203.0.113.10 |
| api | A | 203.0.113.10 |

nginx on the droplet routes each subdomain to the correct app.

### Subdomain to different servers

Each subdomain can point to a different IP:

| Name | Type | Value |
|------|------|-------|
| fwbng | A | 203.0.113.10 (DigitalOcean) |
| shop | A | 104.21.xx.xx (Shopify) |
| mail | MX | mail.provider.com |

### Wildcard subdomain (advanced)

Route ALL subdomains to one server:

| Name | Type | Value |
|------|------|-------|
| * | A | 203.0.113.10 |

Anything.yourdomain.org will resolve to your droplet.

---

## Troubleshooting

### "Server not found" / DNS not resolving

1. Wait longer (DNS propagation)
2. Check you added the record to the correct DNS provider
3. Verify nameservers: `dig NS exploratoryphilology.org`
4. Try flushing local DNS cache:
   ```bash
   # macOS
   sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder

   # Linux
   sudo systemd-resolve --flush-caches
   ```

### DNS resolves but connection refused

1. nginx isn't running: `systemctl status nginx`
2. Firewall blocking port 80/443
3. nginx not configured for this subdomain

### DNS resolves but shows wrong content

1. nginx server_name doesn't match subdomain
2. Check nginx config: `cat /etc/nginx/sites-enabled/fwbng`
3. Reload nginx: `systemctl reload nginx`

### SSL certificate errors

1. DNS must be fully propagated before running certbot
2. Run: `certbot --nginx -d fwbng.exploratoryphilology.org`
3. Ensure nginx has correct server_name

---

## DNS Record Types Reference

| Type | Purpose | Example |
|------|---------|---------|
| **A** | Points domain to IPv4 address | `fwbng` → `203.0.113.10` |
| **AAAA** | Points domain to IPv6 address | `fwbng` → `2001:db8::1` |
| **CNAME** | Alias to another domain | `www` → `exploratoryphilology.org` |
| **MX** | Mail server | `@` → `mail.google.com` |
| **TXT** | Text data (verification, SPF) | Various |

For web hosting, you typically just need **A** records.

---

## Using Cloudflare (Optional Enhancement)

If you want DDoS protection, caching, and easier SSL:

1. Sign up at [cloudflare.com](https://www.cloudflare.com/)
2. Add your domain
3. Update nameservers at your registrar to Cloudflare's
4. Manage DNS in Cloudflare dashboard
5. Enable "Proxied" (orange cloud) for CDN benefits

**Note:** With Cloudflare proxied, your server sees Cloudflare's IP, not the visitor's. May need to configure `X-Forwarded-For` handling.

---

## Quick Checklist

- [ ] Found DNS management panel
- [ ] Added A record: `fwbng` → `YOUR_DROPLET_IP`
- [ ] Waited for DNS propagation
- [ ] Verified with `dig fwbng.exploratoryphilology.org`
- [ ] Confirmed main domain still works
- [ ] nginx configured with matching `server_name`
- [ ] SSL certificate obtained with certbot
