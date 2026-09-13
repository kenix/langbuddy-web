# wordgarner-web

The public site for [Word Garner](https://wordgarner.zhware.org) — the landing
page, the privacy policy, the support page and the terms of use that the App
Store and Google Play require before a build can be submitted.

Plain static HTML. No build step, no dependencies, no JavaScript.

## The mark

A pea pod holding three seeds, on a deep-teal tile. `icon.svg` is the app
icon, with a glyph on each seed (A, あ, 字, as outlines — no font needed);
`favicon.svg` is the same drawing with plain seeds, and is the site's tab
icon and the header's logo, because under 32 px the glyphs only blur.
`favicon.ico` (16/32/48) and `apple-touch-icon.png` (180) are rasters of
those two files, for the browsers and home screens that will not take an
SVG. Everything is committed; after changing the mark, regenerate the
rasters — and, with `--app`, the app's iOS and Android icon sets from the
same files:

```bash
python3 tools/make_icons.py --app ../../apps/wordgarner
```

The icon links carry a `?v=N`, because browsers hold a favicon much longer
than the site asks them to. Bump it in all six pages when the mark changes,
or returning visitors keep the old one.

The name beside the mark is set in Bricolage Grotesque — 2.6 kB in
`assets/fonts/`, cut down to the nine letters of "Word Garner" and served
from this site, never from a font network. It is the only webfont here and
the only thing that uses it is the header. Renaming the site means cutting
a new subset first: the `@font-face` declares the subset's own
`unicode-range`, so a letter it does not contain falls back to the system
sans without a word.

## Preview

```bash
python3 -m http.server 8000
# http://localhost:8000
```

## Publishing on GitHub Pages

1. Push this repository to GitHub.
2. **Settings ▸ Pages ▸ Build and deployment**: source *Deploy from a
   branch*, branch `main`, folder `/ (root)`.
3. **Settings ▸ Pages ▸ Custom domain**: `wordgarner.zhware.org`. The `CNAME`
   file in this repository already carries it, so the field should fill in by
   itself once DNS resolves.
4. At your DNS provider, add a `CNAME` record:

   | Name | Type | Value |
   |---|---|---|
   | `wordgarner` | `CNAME` | `<your-github-username>.github.io` |

5. Back in **Settings ▸ Pages**, tick **Enforce HTTPS** once the certificate
   has been issued (it can take a few minutes after DNS propagates).

## The report form

`/report/` posts to [Web3Forms](https://web3forms.com/), which emails it on
to `wordgarner.support@zhware.org`. GitHub Pages cannot run anything itself,
so the form needs an off-site endpoint.

Register the access key once at <https://web3forms.com/> with
`wordgarner.support@zhware.org` and the website `https://wordgarner.zhware.org/support/`,
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
| Privacy policy URL (Apple, Google) | `https://wordgarner.zhware.org/privacy/` |
| Support URL (Apple) | `https://wordgarner.zhware.org/support/` |
| Marketing URL (Apple, optional) | `https://wordgarner.zhware.org/` |
| Contact email (Google) | `wordgarner.support@zhware.org` |
| EULA (Apple, optional) | `https://wordgarner.zhware.org/terms/` |

## Before submitting

- [ ] Drop store screenshots into `assets/screenshots/` and reference them on
      the landing page (`apps/wordgarner/tool/screenshots.sh` takes them).
- [ ] Add the App Store and Play links to the landing page once the listings
      exist.
- [ ] Re-read `privacy/index.html` against what the app actually does, and
      answer Play's Data safety form the same way.
- [ ] Paste the Web3Forms `access_key` into `report/index.html` and send one
      test report end to end.
- [ ] Look at the landing page on a real phone in both themes. The palette
      moved to the mark's colours (deep teal on light, pea green on dark)
      and only the desktop browser has seen it.
