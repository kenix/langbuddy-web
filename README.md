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

## The report form

`/report/` posts to [Web3Forms](https://web3forms.com/), which emails it on
to `langbuddy.support@zhware.org`. GitHub Pages cannot run anything itself,
so the form needs an off-site endpoint.

Register the access key once at <https://web3forms.com/> with
`langbuddy.support@zhware.org` and the website `https://langbuddy.zhware.org/support/`,
then paste the key into the `access_key` hidden field in `report/index.html`.
The key is public by design — it only says which mailbox to deliver to.

Spam is handled by the **Honeypot Trick**: the hidden `botcheck` checkbox. A
bot ticks it, a person never sees it, and Web3Forms drops the message. No
CAPTCHA in the path.

Two things worth checking against their current documentation before you
rely on them:

- **No attachments.** File uploads are a paid Web3Forms feature, so the form
  is text only and people are pointed at the support address for screenshots.
  Adding a file input back means `enctype="multipart/form-data"`, a paid plan,
  and a line in the privacy policy.
- **The `redirect` field.** It points at `/report/thanks/`, which only works
  once the custom domain is live.

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
- [ ] Paste the Web3Forms `access_key` into `report/index.html` and send one
      test report end to end.
