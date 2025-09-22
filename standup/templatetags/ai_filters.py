import re
from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escape

register = template.Library()

@register.filter
def parse_ai_analysis(summary):
    """
    Parse AI strategic analysis content and return structured HTML
    """
    if not summary:
        return "No AI analysis available"
    
    # Convert markdown-style formatting to HTML
    html_content = escape(summary)
    
    # Convert markdown headers to HTML
    html_content = re.sub(r'^## (.+)$', r'<h6 class="text-primary mt-3 mb-2"><i class="fas fa-brain me-2"></i>\1</h6>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'^\*\*(.+)\*\*$', r'<h6 class="text-dark mt-2 mb-1"><strong>\1</strong></h6>', html_content, flags=re.MULTILINE)
    
    # Convert bold text
    html_content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_content)
    
    # Convert bullet points
    html_content = re.sub(r'^- (.+)$', r'<div class="mb-1 ms-3">• \1</div>', html_content, flags=re.MULTILINE)
    
    # Convert emojis and status indicators
    html_content = re.sub(r'✅', '<i class="fas fa-check-circle text-success me-1"></i>', html_content)
    html_content = re.sub(r'❌', '<i class="fas fa-times-circle text-danger me-1"></i>', html_content)
    html_content = re.sub(r'⚠️', '<i class="fas fa-exclamation-triangle text-warning me-1"></i>', html_content)
    html_content = re.sub(r'🎯', '<i class="fas fa-bullseye text-primary me-1"></i>', html_content)
    html_content = re.sub(r'👥', '<i class="fas fa-users text-info me-1"></i>', html_content)
    html_content = re.sub(r'🔍', '<i class="fas fa-search text-secondary me-1"></i>', html_content)
    html_content = re.sub(r'💭', '<i class="fas fa-comment text-muted me-1"></i>', html_content)
    
    # Convert line breaks to HTML
    html_content = html_content.replace('\n', '<br>')
    
    return mark_safe(html_content)

@register.filter
def extract_ai_section(summary, section_name):
    """
    Extract a specific section from AI analysis
    """
    if not summary:
        return ""
    
    # Define section patterns
    patterns = {
        'strategic_context': r'Strategic Context:(.+?)(?=Performance Patterns:|Risk Assessment:|$)',
        'performance_patterns': r'Performance Patterns:(.+?)(?=Risk Assessment:|Growth Opportunities:|$)',
        'risk_assessment': r'Risk Assessment:(.+?)(?=Growth Opportunities:|Team Velocity:|$)',
        'growth_opportunities': r'Growth Opportunities:(.+?)(?=Team Velocity:|Strategic Pattern:|$)',
        'team_velocity': r'Team Velocity Trends:(.+?)(?=Dependency Mapping:|Strategic Pattern:|$)',
        'dependencies': r'Dependency Mapping:(.+?)(?=Action Items:|Recommendations:|$)'
    }
    
    pattern = patterns.get(section_name.lower())
    if not pattern:
        return ""
    
    match = re.search(pattern, summary, re.DOTALL | re.IGNORECASE)
    if match:
        content = match.group(1).strip()
        # Clean up and format
        content = re.sub(r'^\s*-\s*', '', content, flags=re.MULTILINE)
        content = content.replace('\n', ' ').strip()
        return content[:300] + '...' if len(content) > 300 else content
    
    return ""

@register.filter
def ai_summary_preview(summary, max_length=200):
    """
    Create a clean preview of AI analysis without markdown
    """
    if not summary:
        return "No AI analysis available"
    
    # Remove markdown formatting for preview
    clean_text = re.sub(r'\*\*(.+?)\*\*', r'\1', summary)
    clean_text = re.sub(r'^#+\s*', '', clean_text, flags=re.MULTILINE)
    clean_text = re.sub(r'^-\s*', '', clean_text, flags=re.MULTILINE)
    clean_text = re.sub(r'\n+', ' ', clean_text)
    clean_text = clean_text.strip()
    
    if len(clean_text) > max_length:
        return clean_text[:max_length] + '...'
    return clean_text

@register.filter
def format_markdown(content):
    """
    Convert markdown-style AI analysis to formatted HTML
    """
    if not content:
        return ""
    
    # Early return for already processed HTML content
    if '<div class="bullet-point">' in content and content.startswith('<strong class="text-primary">'):
        return mark_safe(content)
    
    # Clean up unwanted headers and sections BEFORE processing
    # Remove "Strategic Team Standup Analysis" header (various formats)
    content = re.sub(r'^##?\s*Strategic Team Standup Analysis\s*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'^\s*Strategic Team Standup Analysis\s*$', '', content, flags=re.MULTILINE)
    
    # Remove "📈 Strategic Metadata" section and everything after it
    content = re.sub(r'\*\*📈\s*Strategic Metadata\*\*:[\s\S]*$', '', content)
    content = re.sub(r'📈\s*Strategic Metadata:?[\s\S]*$', '', content)
    content = re.sub(r'##?\s*📈\s*Strategic Metadata[\s\S]*$', '', content, flags=re.MULTILINE)
    
    # Remove JSON metadata blocks (more comprehensive)
    content = re.sub(r'\{[\s\S]*?"team_sentiment"[\s\S]*?\}', '', content)
    content = re.sub(r'\{[\s\S]*?"velocity_score"[\s\S]*?\}', '', content)
    content = re.sub(r'\{[\s\S]*?"strategic_priorities"[\s\S]*?\}', '', content)
    
    # Remove any standalone "Strategic Metadata" lines
    content = re.sub(r'^\s*Strategic Metadata\s*:?\s*$', '', content, flags=re.MULTILINE)
    
    # Remove any remaining emoji headers that might have been missed
    content = re.sub(r'^\s*📈.*$', '', content, flags=re.MULTILINE)
    
    # Clean up bullet points that might refer to these sections
    content = re.sub(r'^[•-]\s*Strategic Team Standup Analysis.*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'^[•-]\s*📈.*$', '', content, flags=re.MULTILINE)
    
    # Clean up extra whitespace and empty lines
    content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
    content = re.sub(r'^\s*\n+', '', content)  # Remove leading empty lines
    content = re.sub(r'\n+\s*$', '', content)  # Remove trailing empty lines
    content = content.strip()
    
    # If content is now empty or too short, return empty
    if len(content.strip()) < 10:
        return ""
    
    # Escape HTML first
    html_content = escape(content)
    
    # Convert markdown headers with special handling for blocker analysis
    html_content = re.sub(r'^## (.+)$', r'<h5 class="text-primary mt-3 mb-2">\1</h5>', html_content, flags=re.MULTILINE)
    
    # Convert emojis to icons FIRST
    emoji_map = {
        '✅': '<i class="fas fa-check-circle text-success me-1"></i>',
        '❌': '<i class="fas fa-times-circle text-danger me-1"></i>',
        '⚠️': '<i class="fas fa-exclamation-triangle text-warning me-1"></i>',
        '🎯': '<i class="fas fa-bullseye text-primary me-1"></i>',
        '👥': '<i class="fas fa-users text-info me-1"></i>',
        '🔍': '<i class="fas fa-search text-secondary me-1"></i>',
        '💭': '<i class="fas fa-comment text-muted me-1"></i>',
        '🚀': '<i class="fas fa-rocket text-success me-1"></i>',
        '📊': '<i class="fas fa-chart-bar text-info me-1"></i>',
        '⏰': '<i class="fas fa-clock text-warning me-1"></i>',
        '🚧': '<i class="fas fa-exclamation-triangle text-warning me-1"></i>',
        '💡': '<i class="fas fa-lightbulb text-success me-1"></i>'
    }
    
    for emoji, icon in emoji_map.items():
        html_content = html_content.replace(emoji, icon)
    
    # Add special class for Strategic Blocker Analysis to force column break
    html_content = re.sub(
        r'<h5 class="text-primary mt-3 mb-2"><i class="fas fa-exclamation-triangle text-warning me-1"></i> Strategic Blocker Analysis:</h5>',
        r'<h5 class="text-primary mt-3 mb-2 blocker-analysis-break"><i class="fas fa-exclamation-triangle text-warning me-1"></i> Strategic Blocker Analysis:</h5>',
        html_content
    )
    
    # Handle Strategic Recommendations with special formatting
    html_content = re.sub(
        r'<h5 class="text-primary mt-3 mb-2">Strategic Recommendations:</h5>',
        r'<div class="recommendations-section"><h5 class="text-primary mt-3 mb-2"><i class="fas fa-lightbulb text-success me-1"></i> Strategic Recommendations:</h5>',
        html_content
    )
    
    # Convert headers with parenthetical information
    html_content = re.sub(r'^\*\*(.+?)\*\* \((.+?)\)$', r'<h6 class="text-dark mt-2 mb-1"><strong>\1</strong> <span class="text-muted">(\2)</span></h6>', html_content, flags=re.MULTILINE)
    
    # Convert bold text
    html_content = re.sub(r'\*\*(.+?)\*\*', r'<strong class="text-primary">\1</strong>', html_content)
    
    # Convert bullet points with better formatting - handle AI summary format specifically
    # First handle bullet points with strong text (AI summary format: - **Section:** content)
    html_content = re.sub(r'^-\s*<strong class="text-primary">([^<]+)</strong>\s*(.*)$', 
                         r'<div class="bullet-point"><strong class="text-primary">\1</strong>\2</div>', 
                         html_content, flags=re.MULTILINE)
    
    # Handle remaining bullet points (without strong text)
    html_content = re.sub(r'^-\s*(.+)$', r'<div class="bullet-point">\1</div>', html_content, flags=re.MULTILINE)
    
    # Handle sub-bullet points (indented)
    html_content = re.sub(r'^  -\s*(.+)$', r'<div class="sub-bullet-point">\1</div>', html_content, flags=re.MULTILINE)
    
    # Close the recommendations section div if it exists
    if 'recommendations-section' in html_content:
        html_content += '</div>'
    
    # Convert line breaks to HTML with proper spacing - avoid breaks between bullet points
    html_content = re.sub(r'\n\n+', '</p><p class="mb-2">', html_content)
    
    # Replace single line breaks with <br> but not before/after div elements
    html_content = re.sub(r'\n(?!</div>)(?!<div)', '<br>', html_content)
    html_content = re.sub(r'</div><br>', '</div>', html_content)
    html_content = re.sub(r'<br><div', '<div', html_content)
    
    # Wrap in paragraph tags
    if html_content and not html_content.startswith('<'):
        html_content = f'<p class="mb-2">{html_content}</p>'
    
    return mark_safe(html_content)