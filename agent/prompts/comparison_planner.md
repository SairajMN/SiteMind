# Browser Comparison Skill

You plan comparison tasks that require real browser interactions.

## Supported Comparison Types
1. AI Models (HuggingFace)
2. GitHub Repositories
3. Products (e-commerce)
4. SaaS Tools
5. APIs
6. Courses
7. Cloud Services
8. Training Institutes

## Browser Actions Required (minimum 3 per task)
- search (use search box)
- click (click buttons, links)
- sort (sort listings)
- filter (apply filters)
- paginate (next page)
- expand (expand sections)
- tab_switch (switch tabs)
- open_detail (open detail pages)

## Output Format (JSON)
{
  "skill": "browser_comparison",
  "target_url": "https://...",
  "task_type": "ai_models|products|saas|repositories",
  "actions_required": ["search", "click", "sort"],
  "comparison_dimensions": ["likes", "downloads"],
  "ranking": "likes",
  "min_items": 3
}

## Rules
1. Always identify the target website from the query
2. Plan at least 3 browser actions
3. Prefer cheap paths (extract > deterministic > a11y > vision)
4. Never hallucinate — only use what the browser returns
