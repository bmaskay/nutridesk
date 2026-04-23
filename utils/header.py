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
        """<style>
        /* ── Layout ──────────────────────────────────────────────── */
        section[data-testid='stMain']>div:first-child{padding-top:110px!important}
        header[data-testid='stHeader']{visibility:hidden!important;height:0!important}
        #MainMenu,footer{visibility:hidden!important}

        /* ── Typography ──────────────────────────────────────────── */
        h1,h2,h3{color:#2D6A4F!important;letter-spacing:-0.015em!important}
        h1{font-size:1.55rem!important;font-weight:800!important}
        h2{font-size:1.2rem!important;font-weight:700!important}
        h3{font-size:1rem!important;font-weight:700!important}

        /* ── Sidebar ─────────────────────────────────────────────── */
        [data-testid='stSidebar']{
            background:linear-gradient(180deg,#F5EFE8 0%,#EDE4D8 100%)!important;
            border-right:1px solid #DDD0C2!important;
        }
        section[data-testid='stSidebar']>div:first-child{padding-top:104px!important}
        [data-testid='stSidebarNav'] a{
            color:#374151!important;border-radius:8px!important;
            font-weight:500!important;font-size:0.92rem!important;
            padding:7px 12px!important;transition:all 0.15s ease!important;
            display:block!important;margin:1px 0!important;
        }
        [data-testid='stSidebarNav'] a:hover{
            background:#D8F3DC!important;color:#2D6A4F!important;
            padding-left:16px!important;
        }
        [data-testid='stSidebarNav'] a[aria-current='page']{
            background:#D8F3DC!important;color:#2D6A4F!important;
            font-weight:700!important;border-left:3px solid #2D6A4F!important;
            padding-left:9px!important;
        }

        /* ── Metric cards ────────────────────────────────────────── */
        [data-testid='metric-container']{
            background:#FFFFFF!important;
            border:1px solid #E5D9CC!important;
            border-top:3px solid #40916C!important;
            border-radius:12px!important;
            padding:18px 20px 16px!important;
            box-shadow:0 2px 8px rgba(45,106,79,0.07)!important;
            transition:box-shadow 0.2s ease,transform 0.2s ease!important;
        }
        [data-testid='metric-container']:hover{
            box-shadow:0 6px 22px rgba(45,106,79,0.14)!important;
            transform:translateY(-2px)!important;
        }
        [data-testid='stMetricValue']{
            color:#2D6A4F!important;font-weight:800!important;font-size:1.9rem!important;
        }
        [data-testid='stMetricLabel']{
            color:#6B7280!important;font-size:0.72rem!important;
            font-weight:700!important;text-transform:uppercase!important;
            letter-spacing:0.06em!important;
        }
        [data-testid='stMetricDelta']{font-size:0.8rem!important;}

        /* ── Buttons ─────────────────────────────────────────────── */
        .stButton>button{
            background:#2D6A4F!important;color:#FFFFFF!important;
            border-radius:8px!important;border:none!important;
            font-weight:600!important;font-size:0.88rem!important;
            padding:8px 18px!important;letter-spacing:0.01em!important;
            transition:all 0.18s ease!important;
            box-shadow:0 2px 6px rgba(45,106,79,0.22)!important;
        }
        .stButton>button:hover{
            background:#40916C!important;
            box-shadow:0 4px 14px rgba(45,106,79,0.32)!important;
            transform:translateY(-1px)!important;
        }
        .stButton>button:active{transform:translateY(0)!important;}
        .stButton>button:focus-visible{
            outline:2px solid #52B788!important;outline-offset:2px!important;
        }

        /* ── Form controls ───────────────────────────────────────── */
        [data-baseweb='select']>div{border-radius:8px!important;border-color:#D5CEC6!important;}
        [data-baseweb='input']>div,[data-baseweb='textarea']>div{border-radius:8px!important;}

        /* ── Dividers ────────────────────────────────────────────── */
        hr{border:none!important;border-top:1px solid #E8DDD1!important;margin:1.2rem 0!important;}

        /* ── Expanders ───────────────────────────────────────────── */
        [data-testid='stExpander']>details{
            border:1px solid #E5D9CC!important;border-radius:10px!important;overflow:hidden!important;
        }
        [data-testid='stExpander']>details>summary{
            background:#F9F5EF!important;padding:10px 16px!important;
            font-weight:600!important;color:#2D6A4F!important;font-size:0.92rem!important;
        }
        [data-testid='stExpander']>details>summary:hover{background:#EFE8DE!important;}

        /* ── Alerts ──────────────────────────────────────────────── */
        [data-testid='stAlert']{border-radius:10px!important;border-left-width:4px!important;}

        /* ── DataFrame ───────────────────────────────────────────── */
        [data-testid='stDataFrame']{
            border-radius:10px!important;overflow:hidden!important;
            border:1px solid #E5D9CC!important;
            box-shadow:0 1px 4px rgba(45,106,79,0.06)!important;
        }

        /* ── Tabs ────────────────────────────────────────────────── */
        [data-testid='stTabs'] button[role='tab']{
            border-radius:6px 6px 0 0!important;font-weight:500!important;
            transition:all 0.15s!important;
        }
        [data-testid='stTabs'] button[role='tab'][aria-selected='true']{
            color:#2D6A4F!important;border-bottom-color:#2D6A4F!important;font-weight:700!important;
        }

        /* ── Progress bars ───────────────────────────────────────── */
        [data-testid='stProgress']>div>div{
            background:linear-gradient(90deg,#2D6A4F,#52B788)!important;border-radius:4px!important;
        }
        </style>""",
        unsafe_allow_html=True,
    )

    # ── Banner injected into parent DOM via JS ───────────────────────────────
    page_bit = (
        f'+ \'<span style="font-size:0.68rem;letter-spacing:1.5px;text-transform:uppercase;'
        f'color:rgba(255,255,255,0.65);margin-top:5px;font-family:sans-serif;display:block;'
        f'background:rgba(0,0,0,0.12);padding:3px 10px;border-radius:20px;width:fit-content;margin-left:auto;">'
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
            var lpad = Math.max(sbW + 28, 284) + 'px';

            // ── Build banner ───────────────────────────────────────────────
            var b = parent.document.createElement('div');
            b.id = 'nd-banner';
            b.style.cssText =
                'position:fixed;top:0;left:0;right:0;z-index:999999;'
              + 'background:linear-gradient(135deg,#1E5C40 0%,#2D6A4F 45%,#40916C 100%);'
              + 'height:88px;padding-left:' + lpad + ';padding-right:40px;'
              + 'display:flex;align-items:center;justify-content:space-between;'
              + 'box-shadow:0 4px 20px rgba(30,92,64,0.35);'
              + 'border-bottom:1px solid rgba(255,255,255,0.08);';

            b.innerHTML =
                // Left: logo + wordmark
                '<a href="/" style="text-decoration:none;display:flex;align-items:center;gap:14px;cursor:pointer;">'
              +   '<div style="width:44px;height:44px;border-radius:12px;'
              +              'background:rgba(255,255,255,0.15);backdrop-filter:blur(4px);'
              +              'display:flex;align-items:center;justify-content:center;'
              +              'font-size:1.6rem;line-height:1;flex-shrink:0;'
              +              'border:1px solid rgba(255,255,255,0.2);">'
              +     '&#127807;'
              +   '</div>'
              +   '<div style="display:flex;flex-direction:column;justify-content:center;">'
              +     '<span style="font-size:1.75rem;font-weight:800;color:#FFFFFF;'
              +             'line-height:1.1;letter-spacing:-0.02em;font-family:Georgia,serif;">'
              +       'NutriDesk'
              +     '</span>'
              +     '<span style="font-size:0.75rem;font-weight:600;color:rgba(216,243,220,0.9);'
              +             'text-transform:uppercase;letter-spacing:3px;'
              +             'margin-top:2px;font-family:sans-serif;">'
              +       '\u0100h\u0101ra by Asha'
              +     '</span>'
              +   '</div>'
              + '</a>'
              // Right: handle + optional page tag
              + '<div style="text-align:right;display:flex;flex-direction:column;'
              +             'justify-content:center;align-items:flex-end;gap:4px;">'
              +   '<span style="font-size:0.85rem;font-weight:500;font-style:italic;'
              +           'color:rgba(216,243,220,0.85);font-family:sans-serif;">@Asha.Nutrition</span>'
              {page_bit}
              + '</div>';

            parent.document.body.appendChild(b);

            // Subtle bottom accent line
            var accent = parent.document.createElement('div');
            accent.id = 'nd-banner-accent';
            accent.style.cssText =
                'position:fixed;top:88px;left:0;right:0;z-index:999998;'
              + 'height:3px;'
              + 'background:linear-gradient(90deg,#52B788 0%,#D8F3DC 50%,#52B788 100%);'
              + 'opacity:0.6;';
            parent.document.body.appendChild(accent);

            // Re-adjust on sidebar toggle/resize
            parent.window.addEventListener('resize', function() {{
                var s = parent.document.querySelector('[data-testid="stSidebar"]');
                var w = s ? s.getBoundingClientRect().width : 0;
                var p = Math.max(w + 28, 284) + 'px';
                b.style.paddingLeft = p;
            }});
        }})();
        </script>
        """,
        height=0,
    )
