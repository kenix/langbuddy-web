# wordgarner-web

The public site for the Word Garner app: <https://wordgarner.zhware.org>.

It exists because both stores require it. Apple wants a support URL and a
privacy policy URL before a build can be submitted; Google Play wants a
privacy policy URL and a contact address, and its Data safety form has to be
backed by what the policy says. Everything here is written to be the answer
to one of those.

## Commands

There is no build. It is four HTML files and one stylesheet.

```bash
python3 -m http.server 8000     # preview at http://localhost:8000
```

## Fixed decisions (do not revisit)

- **Static HTML, hand-written, no generator and no dependencies.** The site
  is four pages that change a few times a year. A toolchain would be more
  to maintain than the thing it maintains.
- **No cookies, no analytics, no third-party scripts, no webfonts.** An app
  whose whole pitch is that it does not phone home cannot have a privacy
  page that loads a font from someone else's CDN. The single exception is
  eight lines of our own inline script on the report page, declared in the
  privacy policy.
- **The form posts to Web3Forms.** GitHub Pages serves files and runs
  nothing, so a form needs somewhere off-site to post to. It is a plain
  `<form method="POST">` with no JavaScript in the path, so it still works
  with scripting off; `redirect` is the thank-you page and `botcheck` is the
  Honeypot Trick that keeps the CAPTCHA out of the way. `access_key` is the
  public Web3Forms key for the support mailbox. **It is a third-party data
  flow and the privacy policy says so** — do not add another one without
  adding it there too.
- **The app's own details arrive in the link, not from the browser.** The
  app opens `/report/?d=<diagnostics>`; the page copies that into a
  read-only field so the user sees exactly what will be sent. The browser
  cannot be asked for the app version, and asking a person to copy it by
  hand is asking for the report without it.
- **Hosted on GitHub Pages** at the apex-style custom domain in `CNAME`.
  `.nojekyll` is there so the build never second-guesses the file layout.
- **One stylesheet, light and dark**, driven by `prefers-color-scheme`.
- **One mark, defined once, in SVG.** The mark is a pea pod holding three
  seeds on a deep-teal tile. `icon.svg` is the app icon: each seed carries
  a glyph (A, あ, 字 — the scripts the app renders), converted to outlines
  so the file needs no font. `favicon.svg` is the same drawing with plain
  seeds, and is what the tab and the header show, because under 32 px a
  glyph only muddies its seed. Every raster icon — `favicon.ico`,
  `apple-touch-icon.png`, and with `--app` the app's iOS and Android sets —
  is produced by `tools/make_icons.py`, which *reads* those two SVGs and
  rasterises them (pure standard library, run by hand, output committed):
  32 px and above from `icon.svg`, below from `favicon.svg`. So the shape
  lives in the SVGs only; change it there, rerun the script, commit all of
  it. The tile carries its own background, which is why there is no
  dark-mode variant and no colour rule on `.brand .mark`.

## Layout

| Path | What it is |
|---|---|
| `index.html` | Landing page: what the app is, what it does, store links |
| `privacy/index.html` | Privacy policy — the URL both stores require |
| `support/index.html` | Support page — the URL Apple requires, plus the FAQ |
| `report/index.html` | The bug/idea form, posted to Web3Forms |
| `report/thanks/index.html` | Where Web3Forms sends people afterwards |
| `terms/index.html` | Terms of use / EULA supplement |
| `icon.svg` | The mark with glyphs on the seeds: the app icon, and every raster of 32 px or more |
| `favicon.svg` | The mark with plain seeds: the tab icon *and* the header's |
| `favicon.ico`, `apple-touch-icon.png` | Rasters of the SVGs, written by `tools/make_icons.py` |
| `tools/make_icons.py` | Rasterises the two SVGs; `--app PATH` also writes the app's icon sets. Run by hand, output committed |
| `assets/style.css` | The whole stylesheet |
| `assets/screenshots/` | Store screenshots, as they are taken |
| `CNAME` | `wordgarner.zhware.org` |

Pages live in directories with an `index.html` so the URLs have no `.html`
suffix and a trailing slash works.

## What the store listings need from here

| Field | Value |
|---|---|
| Privacy policy URL (Apple, Google) | `https://wordgarner.zhware.org/privacy/` |
| Support URL (Apple) | `https://wordgarner.zhware.org/support/` |
| Marketing URL (Apple, optional) | `https://wordgarner.zhware.org/` |
| Contact email (Google) | `wordgarner.support@zhware.org` |
| EULA (Apple, optional) | `https://wordgarner.zhware.org/terms/` |

## Keeping it true

The privacy policy is a factual claim about the app, not boilerplate. If the
app ever gains an account, an analytics SDK, a crash reporter, a push
notification, or a server of its own, **this page is wrong until it is
changed**, and the store listing's data-safety answers are wrong with it.
The privacy page's *What might change* section is the one place that looks
forward, and it is a promise as much as a plan: a hosted engine and hosted
storage would be **optional**, and this page is updated **before** either
ships. Do not soften either half.

The claims that would break first:

- "no account and no server"
- "no analytics, advertising or tracking"
- "the only data that ever leaves your device is text you asked to have
  translated"
- "the daily reminder is a local notification … there is no push service"
- "this site sets no cookies, runs no analytics and embeds no third-party
  scripts or fonts"

## Not done yet

- **The wordmark is set in the system sans**, not in the Bricolage
  Grotesque the mark was designed with, because the rule above forbids a
  webfont and the privacy page says so in as many words. A subset of the
  eleven letters of the name, self-hosted, would be a few kilobytes and
  first-party — worth doing if the header ever needs to look drawn rather
  than typed, and not worth breaking the rule quietly for.

## Related

- The app: `apps/wordgarner`. Its Settings ▸ About links here, and its
  support tile opens `/support/`.
- The support address is `wordgarner.support@zhware.org`. It appears on this
  site and in `apps/wordgarner/tools/feedback_endpoint.gs`.
