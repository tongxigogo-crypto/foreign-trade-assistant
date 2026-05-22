# Hongjuda Independent Site

Local standalone website for 苏州宏聚达装饰材料有限公司 / SuZhou hongjuda decorative material co.,ltd.

## Preview

```powershell
cd E:\CodexWorkspace\site-publishing
python -m hongjuda_site.local_server
```

Then open:

- Website: http://127.0.0.1:8144/
- Admin: http://127.0.0.1:8144/admin.html

## Content Editing

- Main editable data: `content/site-content.json`
- Local admin edits call `PUT /api/content`
- Uploaded images are saved to `assets/uploads/`

The admin server is for local editing. Do not expose `admin.html` or the local write APIs as a public production CMS without authentication.

## Model Discovery

The site includes `llms.txt`, `api/openapi.json`, `robots.txt`, `sitemap.xml`, semantic headings and Organization JSON-LD so search engines and AI assistants can identify the company and product categories.
