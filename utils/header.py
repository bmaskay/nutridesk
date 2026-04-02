"""
header.py — Shared fixed green banner + sidebar nav for all NutriDesk pages.
Call render_header() after st.set_page_config() on every page.

Uses JavaScript injection into the parent DOM to bypass Streamlit's
CSS cascade, which strips colour from injected HTML elements.

Sidebar navigation lives here so it persists across all pages automatically.
"""

import streamlit as st
import streamlit.components.v1 as components


def render_header(page_title: str = ""):
    """Inject page CSS, render the fixed green banner via JS, and add sidebar nav."""

    # ── Page-level utility CSS ───────────────────────────────────────────────
    st.markdown(
        "<style>"
        "section[data-testid='stMain']>div:first-child{padding-top:110px!important}"
        "header[data-testid='stHeader']{visibility:hidden!important;height:0!important}"
        "#MainMenu,footer{visibility:hidden!important}"
        "h1,h2,h3{color:#2D6A4F!important}"
        "[data-testid='stSidebar']{background:#FBF7F2!important}"
        "section[data-testid='stSidebar']>div:first-child{padding-top:100px!important}"
        ".stButton>button{background:#2D6A4F;color:#FFFFFF;border-radius:8px;border:none}"
        ".stButton>button:hover{background:#40916C}"
        # Style Streamlit's auto-generated sidebar nav to match brand palette
        "[data-testid='stSidebarNav'] a{color:#2D6A4F!important;border-radius:8px;"
        "  font-weight:500;font-size:0.95rem;}"
        "[data-testid='stSidebarNav'] a:hover{background:#D8F3DC!important;}"
        "[data-testid='stSidebarNav'] a[aria-current='page']{"
        "  background:#D8F3DC!important;font-weight:700!important;}"
        "</style>",
        unsafe_allow_html=True,
    )

    # ── Banner injected into parent DOM via JS ───────────────────────────────
    page_bit = (
        f'+ \'<span style="font-size:0.7rem;letter-spacing:1.2px;text-transform:uppercase;'
        f'color:rgba(255,255,255,0.62);margin-top:4px;font-family:sans-serif;display:block;">'
        f'{page_title}</span>\''
        if page_title else ""
    )

    components.html(
        f"""
        <script>
        (function() {{

            // ── Favicon ────────────────────────────────────────────────────
            var svgFavicon = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
                           + '<text y=".9em" font-size="88">&#127807;</text></svg>';
            var fav = parent.document.querySelector("link[rel~='icon']");
            if (!fav) {{
                fav = parent.document.createElement('link');
                fav.rel = 'icon';
                parent.document.head.appendChild(fav);
            }}
            fav.type = 'image/svg+xml';
            fav.href = 'data:image/svg+xml,' + encodeURIComponent(svgFavicon);

            // ── Remove stale banner on rerun ───────────────────────────────
            var old = parent.document.getElementById('nd-banner');
            if (old) old.remove();

            // ── Sidebar offset ─────────────────────────────────────────────
            var sb = parent.document.querySelector('[data-testid="stSidebar"]');
            var sbW = sb ? sb.getBoundingClientRect().width : 0;
            var lpad = Math.max(sbW + 24, 280) + 'px';

            // ── Build banner ───────────────────────────────────────────────
            var b = parent.document.createElement('div');
            b.id = 'nd-banner';
            b.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:999999;'
                + 'background:linear-gradient(135deg,#2D6A4F 0%,#40916C 100%);'
                + 'height:90px;padding-left:' + lpad + ';padding-right:40px;'
                + 'display:flex;align-items:center;justify-content:space-between;'
                + 'box-shadow:0 3px 14px rgba(45,106,79,0.32);';

            b.innerHTML =
                '<a href="/" style="text-decoration:none;display:flex;align-items:center;gap:12px;cursor:pointer;">'
              +   '<span style="font-size:2rem;line-height:1;">&#127807;</span>'
              +   '<div style="display:flex;flex-direction:column;justify-content:center;">'
              +     '<span style="font-size:1.85rem;font-weight:800;color:#FFFFFF;'
              +             'line-height:1.15;letter-spacing:0.2px;font-family:Georgia,serif;">'
              +       'NutriDesk'
              +     '</span>'
              +     '<span style="font-size:0.82rem;font-weight:600;color:#D8F3DC;'
              +             'text-transform:uppercase;letter-spacing:2.8px;'
              +             'margin-top:3px;font-family:sans-serif;">'
              +       '\u0100h\u0101ra by Asha'
              +     '</span>'
              +   '</div>'
              + '</a>'
              + '<div style="text-align:right;display:flex;flex-direction:column;justify-content:center;">'
              +   '<span style="font-size:0.88rem;font-weight:500;font-style:italic;'
              +           'color:#D8F3DC;font-family:sans-serif;">@Asha.Nutrition</span>'
              {page_bit}
              + '</div>';

            parent.document.body.appendChild(b);

            // Re-adjust on sidebar toggle/resize
            parent.window.addEventListener('resize', function() {{
                var s = parent.document.querySelector('[data-testid="stSidebar"]');
                var w = s ? s.getBoundingClientRect().width : 0;
                b.style.paddingLeft = Math.max(w + 24, 280) + 'px';
            }});
        }})();
        </script>
        """,
        height=0,
    )
