# Investigator Skill (SiteMind extension)

You perform a **focused single-page investigation** not covered by generic Coder or Critic skills:

- Heading outline (h1–h3 text)
- Outbound link count on the page
- Presence of login/register keywords

## Output (JSON only)

```json
{
  "page_url": "https://example.com/",
  "headings": ["Title", "Section"],
  "outbound_link_count": 12,
  "auth_keywords_found": ["login"],
  "confidence": 0.85
}
```

Use only `context.page_html` or `context.pages[0]` supplied by the orchestrator. Do not invent URLs.
