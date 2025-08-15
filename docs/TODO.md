# Paper-QA UI: TODO List

## Current Priority Items

### 1. Fix Answer Formatting
- **Issue**: Answer content is displayed in raw Markdown format instead of rendered HTML
- **Location**: Answer tab content display
- **Solution**: Convert Markdown to HTML for proper rendering
- **Status**: Pending

### 2. Restore Evidence Sections from Research Intelligence
- **Issue**: Some evidence analysis sections were removed during UI reorganization
- **Missing Sections**:
  - Evidence conflicts (previously in Research Intelligence)
  - Key insights (previously in Research Intelligence) 
  - Evidence summary (previously in Research Intelligence)
  - Top evidence by score (previously in Research Intelligence)
- **Solution**: Add these sections back to appropriate tabs (Evidence/Conflicts)
- **Status**: Pending

### 3. Fix Cosmetic Issues
- **Areas to Address**:
  - Tab alignment and spacing
  - Progress indicator colors and states
  - Button styling consistency
  - Text formatting and readability
  - Overall visual polish
- **Status**: Pending

### 4. Improve Documentation for Better Usability
- **Areas to Enhance**:
  - Add step-by-step workflow examples
  - Include troubleshooting section
  - Add configuration examples
  - Improve feature explanations
  - Add best practices section
- **Status**: Pending

## Completed Items

### ✅ Major UI Reorganization
- Consolidated Plan and Retrieval tabs
- Renamed "Response Summary" to "Answer"
- Added dynamic evidence meta summary
- Created dedicated Conflicts tab
- Streamlined Research Intelligence tab
- Removed redundant UI elements

### ✅ Documentation Cleanup
- Updated README.md with current tab structure
- Updated DEVELOPER.md with implementation details
- Added demo video to README
- Documented removed features and defaults

## Future Enhancements

### Performance Optimizations
- Optimize evidence processing pipeline
- Improve real-time progress updates
- Reduce LLM call latency

### Feature Additions
- Export functionality improvements
- Advanced filtering options
- Custom prompt templates
- Batch processing capabilities

### User Experience
- Keyboard shortcuts
- Drag-and-drop file upload
- Session persistence
- Collaborative features

---
*Last Updated: 2025-08-15*
