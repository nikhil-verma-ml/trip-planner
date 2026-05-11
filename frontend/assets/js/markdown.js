/**
 * Simple markdown renderer wrapper
 */
const MarkdownRenderer = {
    render: function(text) {
        if (!text) return "";
        // Use marked library (loaded via CDN in index.html)
        return marked.parse(text);
    }
};
