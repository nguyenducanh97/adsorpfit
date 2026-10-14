# -*- coding: utf-8 -*-
"""Build the password-gated copy of the application.

The published site has two halves. The landing page at the root is public
and is what search engines index. The application itself lives at /app/ as
a single encrypted file behind an ID and password, in the same way as the
BrineFlow site this was asked to match.

How the gate works, and what it is actually worth:

    key        = PBKDF2-HMAC-SHA256(id + "\\n" + password, salt, 310000)
    ciphertext = AES-256-GCM(the whole application, key, iv)

The login page contains only the salt, the iv and the ciphertext. There is
no stored hash to compare against and no branch to skip: an incorrect
password derives a different key, GCM authentication fails, and there is
nothing to show. That is real encryption rather than a JavaScript "if".

What it does not do is make the content secret from someone determined.
The encrypted file is public, so an attacker can try passwords offline as
fast as their hardware allows. The 310000 iterations make each guess
expensive, but a short or dictionary password still falls. Treat this as a
lock on the front door, not as a safe.

Everything is inlined because the application is not one file: the
stylesheets, the seven scripts and the sixteen Python modules would
otherwise still be fetched in the clear from the server, leaving the gate
guarding only the interface. The Python modules are written into a
PY_SOURCES object that js/app.js reads instead of fetching.

Run:  python tools/make_gate.py
      python tools/make_gate.py --dev     also write a readable app/dev.html
"""
import base64
import hashlib
import io
import json
import os
import re
import secrets
import sys

SOURCE = os.path.join("src", "app.html")
OUT_DIR = "app"
ITERATIONS = 310_000

def credentials():
    """The ID and password this build is locked with.

    Deliberately not stored in this file. The repository is public, so a
    password committed here would be readable by exactly the people the
    gate is meant to stop, which would make the whole exercise theatre.
    Supply them through the environment, or be prompted:

        ADSORPFIT_ID=swat ADSORPFIT_PW=... python tools/make_gate.py
    """
    uid = os.environ.get("ADSORPFIT_ID")
    pw = os.environ.get("ADSORPFIT_PW")
    if not uid or not pw:
        import getpass
        uid = uid or input("ID: ").strip()
        pw = pw or getpass.getpass("Password: ")
    if not uid or not pw:
        raise SystemExit("Both an ID and a password are required.")
    return uid, pw


def read(path):
    return io.open(path, encoding="utf-8").read()


def inline_assets(html):
    """Replace every local stylesheet and script with its contents."""
    used = []

    def css(m):
        href = m.group(1).split("?")[0]
        if href.startswith("http"):
            return m.group(0)
        used.append(href)
        return "<style>\n/* %s */\n%s\n</style>" % (href, read(href))

    html = re.sub(r'<link rel="stylesheet" href="([^"]+)"[^>]*>', css, html)

    def js(m):
        src = m.group(1).split("?")[0]
        if src.startswith("http"):
            return m.group(0)
        used.append(src)
        # </script> inside a string would close this block early
        body = read(src).replace("</script>", "<\\/script>")
        return "<script>\n/* %s */\n%s\n</script>" % (src, body)

    html = re.sub(r'<script src="([^"]+)"[^>]*></script>', js, html)
    return html, used


def embed_python(html):
    """Carry the Python modules in the document instead of fetching them."""
    mods = {}
    for name in sorted(os.listdir("py")):
        if name.endswith(".py"):
            mods[name] = read(os.path.join("py", name))
    blob = json.dumps(mods, ensure_ascii=False)
    blob = blob.replace("</script>", "<\\/script>")
    tag = ("<script>\n"
           "/* The Python layer, carried inside this file. js/app.js writes\n"
           "   these straight into the Pyodide filesystem rather than\n"
           "   fetching py/*.py, which do not exist beside this page. */\n"
           "window.PY_SOURCES = " + blob + ";\n</script>\n")
    assert "</head>" in html
    return html.replace("</head>", tag + "</head>", 1), len(mods)


def encrypt(plaintext, login_id, password):
    """PBKDF2 then AES-GCM, matching what the login page performs."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        raise SystemExit(
            "This build needs the 'cryptography' package for AES-GCM.\n"
            "Install it with:  pip install cryptography")
    salt = secrets.token_bytes(16)
    iv = secrets.token_bytes(12)
    key = hashlib.pbkdf2_hmac("sha256",
                              (login_id + "\n" + password).encode("utf-8"),
                              salt, ITERATIONS, dklen=32)
    ct = AESGCM(key).encrypt(iv, plaintext.encode("utf-8"), None)
    return (base64.b64encode(salt).decode(),
            base64.b64encode(iv).decode(),
            base64.b64encode(ct).decode())


SHELL = '''<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>AdsorpFit</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>\U0001f30a</text></svg>">
<style>
 :root{--bg:#060e17;--panel:rgba(12,24,37,.85);--line:#1e394f;--line2:#27506e;
       --ink:#dceaf3;--muted:#7797ac;--accent:#37c8cf;--bad:#ff6058}
 *{box-sizing:border-box}
 body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
      background:radial-gradient(900px 480px at 50% 18%,#0d2233,#04090f 78%);
      color:var(--ink);font:14.5px/1.6 "Segoe UI",system-ui,-apple-system,sans-serif;padding:24px}
 .box{width:min(390px,100%);background:var(--panel);border:1px solid var(--line);
      border-radius:14px;padding:26px 24px;box-shadow:0 24px 70px rgba(0,0,0,.55);
      backdrop-filter:blur(10px)}
 h1{font-size:21px;margin:0 0 3px;letter-spacing:.4px;font-weight:680}
 h1 b{color:var(--accent)}
 .tag{font-size:10.5px;letter-spacing:1.3px;text-transform:uppercase;color:var(--muted);margin:0 0 20px}
 label{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.9px;
       color:var(--muted);font-weight:700;margin:0 0 5px}
 input{width:100%;padding:10px 12px;margin-bottom:14px;border:1px solid var(--line2);
       border-radius:8px;background:#0b1a28;color:var(--ink);font:inherit}
 input:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px rgba(55,200,207,.22)}
 button{width:100%;padding:11px;border:none;border-radius:9px;font:inherit;font-weight:700;
        background:linear-gradient(140deg,var(--accent),#1a93a8);color:#04222a;cursor:pointer}
 button:disabled{opacity:.5;cursor:wait}
 .err{color:var(--bad);font-size:12.5px;margin-top:12px;min-height:18px}
 .ft{margin-top:18px;padding-top:14px;border-top:1px solid var(--line);
     font-size:11.5px;color:var(--muted);text-align:center}
 .ft a{color:var(--accent);text-decoration:none}
</style>
</head>
<body>
<div class="box">
  <h1>Adsorp<b>Fit</b></h1>
  <p class="tag">Adsorption data modelling</p>
  <form id="f">
    <label for="u">ID</label><input id="u" autocomplete="username" autofocus>
    <label for="p">Password</label><input id="p" type="password" autocomplete="current-password">
    <button id="b" type="submit">Open</button>
  </form>
  <div class="err" id="e"></div>
  <div class="ft"><a href="../">About AdsorpFit</a> &middot; a product of
    <a href="http://www.swatlab.or.kr/" target="_blank" rel="noopener">SWAT Lab</a>,
    Sungkyunkwan University</div>
</div>
<script>
const D={s:"__SALT__",i:"__IV__",c:"__CT__"};
const u8=b=>Uint8Array.from(atob(b),c=>c.charCodeAt(0));
document.getElementById('f').addEventListener('submit',async ev=>{
  ev.preventDefault();
  const btn=document.getElementById('b'), err=document.getElementById('e');
  const id=document.getElementById('u').value.trim(), pw=document.getElementById('p').value;
  if(!id||!pw){ err.textContent='Enter both the ID and the password.'; return; }
  btn.disabled=true; err.textContent='Unlocking\\u2026';
  try{
    const base=await crypto.subtle.importKey('raw',new TextEncoder().encode(id+'\\n'+pw),'PBKDF2',false,['deriveKey']);
    const key=await crypto.subtle.deriveKey({name:'PBKDF2',salt:u8(D.s),iterations:__ITER__,hash:'SHA-256'},
                                            base,{name:'AES-GCM',length:256},false,['decrypt']);
    const pt=await crypto.subtle.decrypt({name:'AES-GCM',iv:u8(D.i)},key,u8(D.c));
    const html=new TextDecoder().decode(pt);
    document.open(); document.write(html); document.close();
  }catch(x){
    err.textContent='That ID and password do not match.';
    btn.disabled=false; document.getElementById('p').value=''; document.getElementById('p').focus();
  }
});
</script>
</body>
</html>
'''


def main():
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    html = read(SOURCE)
    html, used = inline_assets(html)
    html, n_mods = embed_python(html)

    leftover = re.findall(r'(?:src|href)="((?!https?:|data:|#|mailto:|tel:)[^"]+)"', html)
    leftover = [p for p in leftover if not p.startswith("../")]
    if leftover:
        print("  note: still referenced relatively: %s" % ", ".join(sorted(set(leftover))))

    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)

    if "--dev" in sys.argv:
        # An unencrypted copy of the entire application. Useful for checking
        # that the bundle assembled correctly, and kept out of git by
        # .gitignore, because publishing it would bypass the gate entirely.
        io.open(os.path.join(OUT_DIR, "dev.html"), "w",
                encoding="utf-8", newline="").write(html)
        print("  wrote app/dev.html (readable, gitignored, local checking only)")

    login_id, password = credentials()
    salt, iv, ct = encrypt(html, login_id, password)
    shell = (SHELL.replace("__SALT__", salt).replace("__IV__", iv)
                  .replace("__CT__", ct).replace("__ITER__", str(ITERATIONS)))
    out = os.path.join(OUT_DIR, "index.html")
    io.open(out, "w", encoding="utf-8", newline="").write(shell)

    print("inlined %d local assets and %d Python modules" % (len(used), n_mods))
    print("bundle   %.0f KB  ->  %s  %.0f KB"
          % (len(html.encode("utf-8")) / 1024, out,
             os.path.getsize(out) / 1024))
    print("locked with ID %r, %d PBKDF2 iterations" % (login_id, ITERATIONS))
    print("the password is not stored anywhere in this repository")


if __name__ == "__main__":
    main()
