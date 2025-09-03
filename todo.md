# Project Todos

## About Singapore Law

### Completed ✅
* ~~Deal with tables input~~ - Fixed: Tables now properly extracted with pipe-separated formatting
* ~~Deal with references at the end of the table~~ - Fixed: Footer content filtering stops processing at references/metadata
* ~~Process content in document order~~ - Fixed: All content types (tables, lists, headings, paragraphs) processed sequentially
* ~~Fix list grouping~~ - Fixed: Pseudo-lists (legal provisions) detected and grouped with bullet points
* ~~Fix paragraph grouping after lists~~ - Fixed: Non-numbered paragraphs after lists attach to previous fragment
* ~~Filter footer content~~ - Fixed: Stops processing at author info, navigation links, disclaimers
* ~~Create GitHub Actions workflows~~ - Complete: Manual-trigger workflows for build/deploy/health-check

### In Progress 🔄
* Figure out whether we can make use of the information of who wrote the article and when it was last updated

### Future Enhancements 💡
* Add metadata extraction for article authors and update dates
* Consider adding chapter cross-references and navigation
* Explore fragment size optimization for better search results
* Add support for additional content types (charts, diagrams)
* Implement content change detection for incremental updates