# Mini-Visionary Audit Report

- Assets: 30
- Referenced assets: 1
- Orphan assets: 30
- Missing references in code: 240
- JS functions called (HTML on*): 39
- JS functions defined: 116
- JS missing implementations: 0
- Flask routes discovered: 20

## Flask routes discovered:
- `/`
- `/<path:path>`
- `/auth.html`
- `/change-password`
- `/create`
- `/forgot-password`
- `/generate`
- `/login`
- `/logo.png`
- `/me`
- `/privacy.html`
- `/profile/upload_ARCHIVED`
- `/profile_ARCHIVED_USE_API_PROFILE_INSTEAD`
- `/register`
- `/static/<path:filename>`
- `/stream`
- `/terms.html`
- `/update`
- `/upload`
- `/uploads/<path:name>`

## Orphan assets (safe to archive if truly unused):
- backend/static/categories/action.jpg
- backend/static/categories/anime.jpg
- backend/static/categories/anime_anime-fox-dragonflame_1024x1536.jpg
- backend/static/categories/fantasy1.jpg
- backend/static/categories/fantasy_angel-vs-demon-dual_1024x1536.jpg
- backend/static/categories/fantasy_angelic-paladin-flamesword_1024x1536.jpg
- backend/static/categories/fantasy_cute-celestial-mage_1024x1024.jpg
- backend/static/categories/fantasy_dark-angel_1024x1536.jpg
- backend/static/categories/fantasy_dark-knight-flame_1024x1536.jpg
- backend/static/categories/fantasy_elemental-fairy-firewater_1024x1536.jpg
- backend/static/categories/fantasy_fantasy-castle-themepark_1024x1024.jpg
- backend/static/categories/fantasy_halo-dualblades-sentinel_1024x1536.jpg
- backend/static/categories/fantasy_halo-spear-guardian_1024x1536.jpg
- backend/static/categories/fantasy_light-angel_1024x1536.jpg
- backend/static/categories/fantasy_rune-wolf-storm_1024x1536.jpg
- backend/static/categories/fantasy_spirit-wolf-aura_1024x1536.jpg
- backend/static/categories/horror_cerberus-hellhound_1024x1536.jpg
- backend/static/categories/horror_dark-reaper-angel_1024x1536.jpg
- backend/static/categories/horror_pumpkin-rider_1024x1536.jpg
- backend/static/categories/romance.jpg
- backend/static/categories/scifi.jpg
- backend/static/categories/scifi_cybernetic-tiger-cub_1024x1024.jpg
- backend/static/favicon.ico
- backend/static/home-logo.png
- backend/static/logo.png
- backend/static/visionary-favicon-128x128.png
- backend/static/visionary-favicon-16x16.png
- backend/static/visionary-favicon-32x32.png
- backend/static/visionary-favicon-48x48.png
- backend/static/visionary-favicon-64x64.png

## Missing references (likely broken links/paths):
-  http://example.com 
- ${img.url}
- ${item.to}
- ${item.url}
- ${msg.imageUrl}
- ${post.imageUrl}
- ${profilePicUrl}
- ${profilePic}
- **parts
- *,
    strip_whitespace: bool = True,
    min_length: int = 1,
    max_length: int = 2**16,
    tld_required: bool = True,
    host_required: bool = True,
    allowed_schemes: Optional[Collection[str]] = None,

- _absolute_link_url(base_url, href
- _absolute_link_url(page_url, file_url
- api/account_sessions
- asgi_scope, default_scheme, host
- aws_context, start_time
- aws_event, aws_context
- base_url, config
- base_url: str, url: str
- cfg
- class_attributes, **kwargs
- client, host
        
- client, url
- client_config=client_config,
            endpoint_url=endpoint_url,
        
- client_endpoint_url
        
- cls
- cls, fee, sid
- cls, id, nested_id=None
- cls, location: str
- cls, sid
- cls, uri: str
- cls, url
- cls, url: Any, info: core_schema.SerializationInfo
- connect/custom-accounts
- create
- db_url
- defaults[data]
- docs/billing/subscriptions/usage-based
- docs/payments/payment-intents
- docs/payments/save-and-reuse
- editable_project_location
- endpoint_type
- endpoint_url
- endpoint_url
    
- endpoint_url
        
- entry.path
- environ
- environ, strip_querystring=True
- environ, use_x_forwarded_for
- environ, use_x_forwarded_for=False
- environ: WSGIEnvironment,
    root_only: bool = False,
    strip_querystring: bool = False,
    host_only: bool = False,
    trusted_hosts: t.Iterable[str] | None = None,

... and 190 more (see audit.json)

## JS functions used in HTML but not defined (wire up or remove):