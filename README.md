# langbuddy-web

The public site for [LangBuddy](https://langbuddy.zhware.org) — the landing
page, the privacy policy, the support page and the terms of use that the App
Store and Google Play require before a build can be submitted.

Plain static HTML. No build step, no dependencies, no JavaScript.

## Preview

```bash
python3 -m http.server 8000
# http://localhost:8000
```

## Publishing on GitHub Pages

1. Push this repository to GitHub.
2. **Settings ▸ Pages ▸ Build and deployment**: source *Deploy from a
   branch*, branch `main`, folder `/ (root)`.
3. **Settings ▸ Pages ▸ Custom domain**: `langbuddy.zhware.org`. The `CNAME`
   file in this repository already carries it, so the field should fill in by
   itself once DNS resolves.
4. At your DNS provider, add a `CNAME` record:

   | Name | Type | Value |
   |---|---|---|
   | `langbuddy` | `CNAME` | `<your-github-username>.github.io` |

5. Back in **Settings ▸ Pages**, tick **Enforce HTTPS** once the certificate
   has been issued (it can take a few minutes after DNS propagates).

## URLs the store listings need

| Field | Value |
|---|---|
| Privacy policy URL (Apple, Google) | `https://langbuddy.zhware.org/privacy/` |
| Support URL (Apple) | `https://langbuddy.zhware.org/support/` |
| Marketing URL (Apple, optional) | `https://langbuddy.zhware.org/` |
| Contact email (Google) | `langbuddy.support@zhware.org` |
| EULA (Apple, optional) | `https://langbuddy.zhware.org/terms/` |

## Before submitting

- [ ] Drop store screenshots into `assets/screenshots/` and reference them on
      the landing page (`apps/langbuddy/tool/screenshots.sh` takes them).
- [ ] Add the App Store and Play links to the landing page once the listings
      exist.
- [ ] Re-read `privacy/index.html` against what the app actually does, and
      answer Play's Data safety form the same way.
