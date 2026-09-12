# langbuddy-web

The public site for the LangBuddy app: <https://langbuddy.zhware.org>.

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
  page that loads a font from someone else's CDN. This is also what lets
  the privacy policy say "this site sets no cookies" without qualification.
- **Hosted on GitHub Pages** at the apex-style custom domain in `CNAME`.
  `.nojekyll` is there so the build never second-guesses the file layout.
- **One stylesheet, light and dark**, driven by `prefers-color-scheme`.

## Layout

| Path | What it is |
|---|---|
| `index.html` | Landing page: what the app is, what it does, store links |
| `privacy/index.html` | Privacy policy — the URL both stores require |
| `support/index.html` | Support page — the URL Apple requires, plus the FAQ |
| `terms/index.html` | Terms of use / EULA supplement |
| `assets/style.css` | The whole stylesheet |
| `assets/screenshots/` | Store screenshots, as they are taken |
| `CNAME` | `langbuddy.zhware.org` |

Pages live in directories with an `index.html` so the URLs have no `.html`
suffix and a trailing slash works.

## What the store listings need from here

| Field | Value |
|---|---|
| Privacy policy URL (Apple, Google) | `https://langbuddy.zhware.org/privacy/` |
| Support URL (Apple) | `https://langbuddy.zhware.org/support/` |
| Marketing URL (Apple, optional) | `https://langbuddy.zhware.org/` |
| Contact email (Google) | `langbuddy.support@zhware.org` |
| EULA (Apple, optional) | `https://langbuddy.zhware.org/terms/` |

## Keeping it true

The privacy policy is a factual claim about the app, not boilerplate. If the
app ever gains an account, an analytics SDK, a crash reporter, a push
notification, or a server of its own, **this page is wrong until it is
changed**, and the store listing's data-safety answers are wrong with it.
The claims that would break first:

- "no account and no server"
- "no analytics, advertising or tracking"
- "the only data that ever leaves your device is text you asked to have
  translated"
- "the daily reminder is a local notification … there is no push service"
- "this site sets no cookies, runs no analytics and embeds no third-party
  scripts or fonts"

## Related

- The app: `apps/langbuddy`. Its Settings ▸ About links here, and its
  support tile opens `/support/`.
- The support address is `langbuddy.support@zhware.org`. It appears on this
  site and in `apps/langbuddy/tools/feedback_endpoint.gs`.
